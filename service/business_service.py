from algo.gemini import Gemini
import shortuuid
import json
import time
from threading import Thread, Lock

from utils.log import get_logger
from utils.config import config as config
from dao.agent_dao import new_agent_history_db, query_agent_history_db

logger = get_logger(config['log']['business_log_file'])

def history_hooks(llm_func):
    def wrapper(*args, **kwargs):
        res, prompt, tag, sess_id = llm_func(*args, **kwargs)
        save_res = res
        if type(res) is not str:
            save_res = json.dumps(res, ensure_ascii=False)
        ## save db
        # logger.info(f'show tag: {tag}, {json.dumps(tag)}')
        new_agent_history_db(sess_id=sess_id, prompt=prompt, tag=tag, response=save_res, llm_type='gemini')
        return res
    return wrapper

class BusinessConsultant:
    def __init__(self, manual_id=None):
        self._id = shortuuid.uuid() if not manual_id else manual_id
        self._expired = time.time()
        logger.info(f'consultant [{self._id}] checkin')

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
                'prompt': prompt,
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
                    tgt_company_info = self._find_tgt_company(src_company=src_company, target_region=target_region, job=job, jd=question)
                    keywords = self._platform_keyword(job=job, jd=question, platform=platform)
                    return {
                        'id': self._id,
                        'target_company': tgt_company_info,
                        'keyword': keywords,
                    }
                else:
                    res = self._first_chat(src_company=src_company, target_region=target_region, job=job, question=question)
        else:
            res = self._continue_chat(question=question)
        return {
            'id': self._id,
            'msg': res,
            'type': 'markdown'
        }
        
    def _judge_jd(self, question):
        prompt = f'请鉴别以下内容是否是一个岗位的jd，直接回复 是 或者 不是\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        res_msg = res_msg.replace('\n','').replace(' ','')
        logger.info(f'consultant [{self._id}] _judge_jd ({prompt}), got: {res_msg}')
        assert res_msg=='是' or res_msg=='不是', f"business internel error, _judge_jd should return 是 or 不是, but got: {res_msg}"
        return res_msg=='是'

    @history_hooks
    def _continue_chat(self, question):
        assert hasattr(self, '_llm'), "business internel error, continue chat without llm object"
        res_msg = self._llm.send_message(prompt=question)
        logger.info(f'consultant [{self._id}] _continue_chat ({question}), got: {res_msg}')
        return res_msg, question, {'msg': question}, self.id

    @history_hooks
    def _first_free_chat(self, question):
        prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。请针对以下问题做出回答\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        logger.info(f'consultant [{self._id}] _first_free_chat ({prompt}), got: {res_msg}')
        return res_msg, prompt, {'msg': question}, self.id

    @history_hooks
    def _first_chat(self, src_company, target_region, job, question):
        prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请针对以下问题做出回答\n{question}'
        res_msg = self._llm.send_message(prompt=prompt)
        logger.info(f'consultant [{self._id}] _first_chat ({question}), got: {res_msg}')
        return res_msg, prompt, {'src_company': src_company, 'target_region': target_region, 'job': job, 'msg': question}, self.id

    @history_hooks
    def _find_tgt_company(self, src_company, target_region, job, jd):
        prompt = f'你是一位针对中国公司海外业务的咨询顾问，你的工作是根据你的专业知识和网络讯息解答问题。公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请给我合适的目标公司，需要以json的list返回目标公司中文名称的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍：\n{jd}'
        res_msg = self._llm.send_message(prompt=prompt)
        tgt_company_info = res_msg
        try:
            tgt_company_info = json.loads(res_msg.replace("```json\n", "").replace("```",""))
        except BaseException as e:
            logger.info(f'_find_tgt_company: parse from ({res_msg}) err: {e}, will return directly')
        logger.info(f'consultant [{self._id}] _find_tgt_company ({prompt}), got: {tgt_company_info}')
        return tgt_company_info, prompt, {'src_company': src_company, 'target_region': target_region, 'job': job, 'jd': jd}, self.id

    @history_hooks
    def _platform_keyword(self, job, jd, platform='领英'):
        prompt = f'匹配这个岗位 {job}，列出搜索简历跟业务相关的英文关键词，方便我在 {platform} 做搜索，需要以json的list返回关键词的列表。请特别注意，只需要这个列表，不需要额外的解释，并且列表长度不要超过15。以下是岗位介绍\n{jd}'
        res_msg = self._llm.send_message(prompt=prompt)
        keywords = res_msg
        try:
            keywords = json.loads(res_msg.replace("```json\n", "").replace("```",""))
        except BaseException as e:
            logger.info(f'_platform_keyword: parse from ({res_msg}) err: {e}, will return directly')
        logger.info(f'consultant [{self._id}] _platform_keyword ({prompt}), got: {keywords}')
        return keywords, prompt, {'job': job, 'jd': jd, 'platform': platform}, self.id

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

    def _get_consultant(self, consultant_id=None):
        with self._lock:
            if consultant_id is None:
                new_consultant = BusinessConsultant()
                self._consultants[new_consultant._id] = new_consultant
                consultant_id = new_consultant._id
            try:
                return self._consultants[consultant_id]
            except BaseException as e:
                logger.info(f"ConsultingFirm _get_consultant ({consultant_id}) exception: {e}, will recreate")
                new_consultant = BusinessConsultant(consultant_id)
                self._consultants[new_consultant._id] = new_consultant
                consultant_id = new_consultant._id
                return self._consultants[consultant_id]

_consulting_firm = ConsultingFirm()

def get_consultant(consultant_id=None):
    global _consulting_firm
    return _consulting_firm._get_consultant(consultant_id=consultant_id)
