import copy

from algo.gemini import Gemini
import shortuuid
import json
import time
from threading import Thread, Lock
import uuid

from utils.log import get_logger
from utils.config import config as config
from dao.agent_dao import *
from service.llm_agent_service import *

logger = get_logger(config['log']['business_log_file'])


def del_history_service(consultant_id):
    mask_history_db(consultant_id)


def session_query_service(user_id):
    sess_list = query_agent_sess_db(manage_account_id=user_id)
    ret_list = []
    for item in sess_list:
        sess_id = item[0]
        round_cnt = query_history_count_db(sess_id)
        title = ''
        if round_cnt > 0:
            first_prompt, first_tag = query_first_history_db(sess_id)
            logger.info(f'session_query_service: {sess_id}, {first_prompt}, {first_tag}')
            first_tag = json.loads(first_tag.replace('\n', ''))
            title = ''
            try:
                if 'jd' in first_tag:
                    title = first_tag['jd'][:50]
                else:
                    title = first_tag['msg'][:50]
            except BaseException as e:
                logger.warning(f"session_query_service parse title from tag failed: {first_tag}")
        ret_list.append(
            {'sess_id': sess_id, 'title': title, 'round_cnt': round_cnt}
        )
    return ret_list


def history_hooks(llm_func):
    def wrapper(*args, **kwargs):
        res, prompt, tag, user_id, sess_id = llm_func(*args, **kwargs)
        save_res = res
        if type(res) is not str:
            save_res = json.dumps(res, ensure_ascii=False)
        ## save db
        # logger.info(f'show tag: {tag}, {json.dumps(tag)}')
        new_agent_history_db(manage_account_id=user_id, sess_id=sess_id, prompt=prompt, tag=tag, response=save_res,
                             llm_type='gemini')
        return res

    return wrapper


class BusinessConsultant:
    def __init__(self, user_id, manual_id=None):
        self._user = user_id
        self._id = shortuuid.uuid() if not manual_id else manual_id
        self._restore_llm_history(manual_id=manual_id)
        self._expired = time.time()
        logger.info(f'consultant({self._user}) [{self._id}] checkin')

    @property
    def id(self):
        return self._id

    def history(self):
        db_history = query_agent_history_db(self.id)
        ret_list = []
        for prompt, tag, response in db_history:
            # with open('tag.json','w') as f:
            #     f.write(tag)
            tag = tag.replace('\n', '。')
            ret_list.append({
                'tag': json.loads(tag),
                'response': response
            })
        return ret_list

    def __call__(self, src_company, target_region, job, question, platform='领英'):
        self._expired = time.time()
        if not hasattr(self, '_llm'):
            self._llm = Gemini()
            ## if no spec for this field, free chat
            if src_company is None or target_region is None or job is None:
                res = self._first_free_chat(question=question)
            else:
                ## if is jd, analysis target company and fetch keyword for jd, if not, free consultent
                query_jd = self._judge_jd(question=question)
                if query_jd:
                    # tgt_company_info = self._find_tgt_company(src_company=src_company, target_region=target_region, job=job, jd=question)
                    # keywords = self._platform_keyword(job=job, jd=question, platform=platform)
                    # return {
                    #     'id': self._id,
                    #     'target_company': tgt_company_info,
                    #     'keyword': keywords,
                    # }
                    return self._tgt_company_and_platform_keyword(src_company=src_company, target_region=target_region,
                                                                  job=job, jd=question, platform=platform)
                else:
                    res = self._first_chat(src_company=src_company, target_region=target_region, job=job,
                                           question=question)
        else:
            res = self._continue_chat(question=question)
        return {
            'id': self._id,
            'msg': res,
            'type': 'markdown'
        }

    def _restore_llm_history(self, manual_id):
        if manual_id is None:
            return
        llm_history = []
        db_history = query_agent_history_db(manual_id)
        for prompt, _, response in db_history:
            llm_history.append({'role': 'user', 'parts': [prompt]})
            llm_history.append({'role': 'model', 'parts': [response]})
        logger.info(f'_restore_llm_history for {manual_id}, init_history len: {len(llm_history)}')
        self._llm = Gemini(init_history=llm_history)

    def _judge_jd(self, question):
        prompt = f'请鉴别以下内容是否是一个岗位的jd，直接回复 是 或者 不是\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        res_msg = res_msg.replace('\n', '').replace(' ', '')
        logger.info(f'consultant [{self._id}] _judge_jd ({prompt}), got: {res_msg}')
        assert res_msg == '是' or res_msg == '不是', f"business internel error, _judge_jd should return 是 or 不是, but got: {res_msg}"
        return res_msg == '是'

    @history_hooks
    def _continue_chat(self, question):
        assert hasattr(self, '_llm'), "business internel error, continue chat without llm object"
        res_msg = self._llm.send_message(prompt=question)
        logger.info(f'consultant [{self._id}] _continue_chat ({question}), got: {res_msg}')
        return res_msg, question, {'msg': question, 'type': 'normal'}, self._user, self.id

    @history_hooks
    def _first_free_chat(self, question):
        prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。请针对以下问题做出回答\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        logger.info(f'consultant [{self._id}] _first_free_chat ({prompt}), got: {res_msg}')
        return res_msg, prompt, {'msg': question, 'type': 'normal'}, self._user, self.id

    @history_hooks
    def _first_chat(self, src_company, target_region, job, question):
        prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请针对以下问题做出回答\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        logger.info(f'consultant [{self._id}] _first_chat ({question}), got: {res_msg}')
        return res_msg, prompt, {'src_company': src_company, 'target_region': target_region, 'job': job,
                                 'msg': question, 'type': 'normal'}, self._user, self.id

    @history_hooks
    def _tgt_company_and_platform_keyword(self, src_company, target_region, job, jd, platform='领英'):
        ## _find_tgt_company
        prompt_tgt_company = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请给我合适的目标公司，需要以json的list返回目标公司中文名称的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍：\n{jd}'
        res_msg = self._llm.send_message(prompt=prompt_tgt_company)
        tgt_company_info = res_msg
        try:
            tgt_company_info = json.loads(res_msg.replace("```json\n", "").replace("```", ""))
        except BaseException as e:
            logger.info(f'_find_tgt_company: parse from ({res_msg}) err: {e}, will return directly')
        logger.info(f'consultant [{self._id}] _find_tgt_company ({prompt_tgt_company}), got: {tgt_company_info}')

        prompt_keyword = f'匹配这个岗位 {job}，列出搜索简历跟业务相关的英文关键词，方便我在 {platform} 做搜索，需要以json的list返回关键词的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍\n{jd}'
        res_msg = self._llm.send_message(prompt=prompt_keyword)
        keywords = res_msg
        try:
            keywords = json.loads(res_msg.replace("```json\n", "").replace("```", ""))
        except BaseException as e:
            logger.info(f'_platform_keyword: parse from ({res_msg}) err: {e}, will return directly')
        logger.info(f'consultant [{self._id}] _platform_keyword ({prompt_keyword}), got: {keywords}')

        compose_prompt = f'{prompt_tgt_company}\n\n\n\n\n{prompt_keyword}'
        ret_msg = {
            'id': self._id,
            'target_company': tgt_company_info,
            'keyword': keywords
        }
        return ret_msg, compose_prompt, {'src_company': src_company, 'target_region': target_region, 'job': job,
                                         'jd': jd, 'platform': platform, 'type': 'analysis'}, self._user, self.id

    # @history_hooks
    # def _find_tgt_company(self, src_company, target_region, job, jd):
    #     prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请给我合适的目标公司，需要以json的list返回目标公司中文名称的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍：\n{jd}'
    #     res_msg = self._llm.send_message(prompt=prompt)
    #     tgt_company_info = res_msg
    #     try:
    #         tgt_company_info = json.loads(res_msg.replace("```json\n", "").replace("```",""))
    #     except BaseException as e:
    #         logger.info(f'_find_tgt_company: parse from ({res_msg}) err: {e}, will return directly')
    #     logger.info(f'consultant [{self._id}] _find_tgt_company ({prompt}), got: {tgt_company_info}')
    #     return tgt_company_info, prompt, {'src_company': src_company, 'target_region': target_region, 'job': job, 'jd': jd, 'type': 'normal'}, self._user, self.id

    # @history_hooks
    # def _platform_keyword(self, job, jd, platform='领英'):
    #     prompt = f'匹配这个岗位 {job}，列出搜索简历跟业务相关的英文关键词，方便我在 {platform} 做搜索，需要以json的list返回关键词的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍\n{jd}'
    #     res_msg = self._llm.send_message(prompt=prompt)
    #     keywords = res_msg
    #     try:
    #         keywords = json.loads(res_msg.replace("```json\n", "").replace("```",""))
    #     except BaseException as e:
    #         logger.info(f'_platform_keyword: parse from ({res_msg}) err: {e}, will return directly')
    #     logger.info(f'consultant [{self._id}] _platform_keyword ({prompt}), got: {keywords}')
    #     return keywords, prompt, {'job': job, 'jd': jd, 'platform': platform}, self._user, self.id


class ConsultingFirm:
    def __init__(self):
        self._consultants = {}
        self._lock = Lock()
        self._thd = Thread(target=self._manage_task)
        self._thd.start()

    def _manage_task(self):
        while True:
            logger.info(f'#### show active consultants: {list(self._consultants.keys())}')
            with self._lock:
                ids = self._consultants.keys()
                for consultant_id in ids:
                    if time.time() - self._consultants[consultant_id]._expired >= config['business']['expired_time_s']:
                        logger.info(f'ConsultingFirm clear expired ({consultant_id})')
                        self._consultants.pop(consultant_id)
            time.sleep(120)

    def _get_consultant(self, user_id, consultant_id=None):
        with self._lock:
            if consultant_id is None:
                new_consultant = BusinessConsultant(user_id=user_id)
                self._consultants[new_consultant._id] = new_consultant
                consultant_id = new_consultant._id
            try:
                return self._consultants[consultant_id]
            except BaseException as e:
                logger.info(
                    f"ConsultingFirm _get_consultant ({user_id}, {consultant_id}) exception: {e}, will recreate from db history")
                new_consultant = BusinessConsultant(user_id=user_id, manual_id=consultant_id)
                self._consultants[new_consultant._id] = new_consultant
                consultant_id = new_consultant._id
                return self._consultants[consultant_id]


_consulting_firm = ConsultingFirm()


def get_consultant(user_id, consultant_id=None):
    global _consulting_firm
    return _consulting_firm._get_consultant(user_id, consultant_id=consultant_id)


def agent_history_remove_service(user_id, session_id):
    update_chat_history_visible(user_id, session_id)


def agent_history_list_service(user_id):
    rows = query_chat_history(user_id)
    history_list = []
    for row in rows:
        session_id, history = row
        msg = json.loads(history)[0]["msg"]
        title = msg[:20]
        history_list.append({"session_id": session_id, "title": title})

    return history_list


def generate_session_id():
    return uuid.uuid4()


def transfer_history_msgs(history_msgs):
    return history_msgs[-10:]


def append_msg(user_id, session_id, history_raw, msg, return_msg):
    if history_raw is not None:
        history_msgs = json.loads(history_raw)
    else:
        history_msgs = []

    history_msgs.append({
        "role": "user",
        "msg": msg
    })
    history_msgs.append({
        "role": "robot",
        "msg": return_msg
    })

    if history_raw is not None:
        update_history_msgs(user_id, session_id, json.dumps(history_msgs, ensure_ascii=False))
    else:
        add_history_msgs(user_id, session_id, json.dumps(history_msgs, ensure_ascii=False))


def agent_chat_service(user_id, session_id, msg):
    if session_id is None or len(session_id) == 0:
        session_id = generate_session_id()

    history_raw = get_history_msgs(user_id, session_id)
    if history_raw is None:
        history_msgs = []
    else:
        history_msgs = json.loads(history_raw)
    history_msgs = transfer_history_msgs(history_msgs)
    msgs = copy.deepcopy(history_msgs)
    msgs.append({
        "role": "user",
        "msg": msg
    })

    chat_intention = ChatIntention()
    intention = chat_intention.judge(msgs)
    logger.info(f"agent_chat_service user_id: {user_id} session_id: {session_id} msgs: {msgs} intention: {intention}")
    if intention == Intention.Normal:
        chat_agent = ChatAgent()
        return_msg = chat_agent.chat("", history_msgs, msg)
        logger.info(
            f"normal chat user_id: {user_id} session_id: {session_id} history_msgs: {history_msgs} return_msg: {return_msg}")
        append_msg(user_id, session_id, history_raw, msg, return_msg)
        return return_msg

    return ""


if __name__ == "__main__":
    msg = agent_chat_service('test', 'test', 'hi')
    print(f"return msg: {msg}")
