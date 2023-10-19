from .base_robot import BaseChatRobot, ChatStatus
from utils.config import config
from utils.log import  get_logger
from utils.utils import format_time

from datetime import datetime
import json
from dao.task_dao import get_job_by_id,query_chat_db

logger = get_logger(config['log']['log_file'])

class MaimaiRobot(BaseChatRobot):
    def __init__(self, robot_api, account_id, job_id, candidate_id, source=None):
        super(MaimaiRobot, self).__init__(robot_api, account_id, job_id, candidate_id, source)
        self._job_id = job_id
        job_config = json.loads(get_job_by_id(job_id)[0][6],strict=False)
        self._preset_reply_dict['hello'] = [job_config['touch_msg']]
        logger.info(f"maimai robot init, preset touch msg: {self._manual_response('hello')}")

    def contact(self, page_history_msg, db_history_msg):
        is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, cur_has_contact, has_manual_touch = \
                self._preprocess(page_history_msg, db_history_msg)
        need_hello = chat_round==0 ##没有用户消息，发生于用户同意好友申请但并未回复消息
        need_contact = need_hello or (chat_round==1 and not has_manual_touch)
        need_use_model = (not user_msg_useless) and (not need_hello)
        self._status = ChatStatus.NormalChat

        model_response = None
        contact_res = None
        model_judge_intent = None
        is_trivial_intent = False
        is_refuse_intent = False
        is_no_prompt = False

        if need_use_model:
            contact_res = self._chat_request()
        if contact_res:
            model_response, model_judge_intent = contact_res
            is_trivial_intent = model_judge_intent in self._trivial_intent
            is_refuse_intent = model_judge_intent in self._refuse_intent
            is_no_prompt = self._is_no_prompt_case(model_response)

        to_cover_response = user_msg_useless or need_hello or is_trivial_intent or is_refuse_intent or is_no_prompt

        strategy_response = None
        chat_info = query_chat_db(self._account_id, self._job_id, self._candidate_id)
            
        if len(chat_info) == 0:
            strategy_response = self._manual_response('hello')
        elif need_hello and chat_info[0][0] == 'user_ask':
            strategy_response = self._manual_response('hello')
        elif need_contact:
            self._status= ChatStatus.NeedContact
            if is_refuse_intent:
                strategy_response = self._manual_response('need_contact_on_refuse')
            else:
                strategy_response = self._manual_response('need_contact_normal')
        else:
            if cur_has_contact:
                strategy_response = self._manual_response('got_contact')
            elif is_trivial_intent or is_refuse_intent or user_msg_useless:
                strategy_response = self._manual_response('trivial_case')
            elif is_no_prompt:
                strategy_response = self._manual_response('no_prompt_case')
        if need_use_model and contact_res is None:
            self._status = ChatStatus.AlgoAbnormal
            model_judge_intent = 'algo_abnormal'

        self._next_msg = model_response if model_response is not None else ''
        if to_cover_response:
            self._next_msg = strategy_response if strategy_response is not None else ''
        else:
            if len(self._next_msg)>0:
                self._next_msg+= '\n'
            self._next_msg += strategy_response if strategy_response is not None else ''
        ##增加换行，前端分多次发出
        self._next_msg = self._next_msg.replace('。','。\n')
        self._next_msg = self._next_msg.replace('.','.\n')
        logger.info(f'maimai chat log {self._sess_id}: info: robot_api: {self._robot_api}, source: {self._source}; \
            tmp: system_msgs: {self._last_system_msgs}, user msgs: {self._last_user_msg}, user msg useless: {user_msg_useless}, \
            is_first: {is_first_msg}, user ask: {user_ask}, chat round: {chat_round}, cur has contact: {cur_has_contact}, has manual touch: {has_manual_touch} \
                need contact: {need_contact}, need user algo: {need_use_model}, algo intent: {model_judge_intent},  \
                    is no prompt: {is_no_prompt}, is trivial: {is_trivial_intent}, is refuse: {is_refuse_intent}, to cover: {to_cover_response}, \
                        model response: {model_response}, strategy response: {strategy_response}; \
                            finally: {self._status}, {self._next_msg}')

        self._msg_list.append({
            'speaker':'robot', 'msg': self._next_msg, 'algo_judge_intent': model_judge_intent, 'time': format_time(datetime.now())
        })


    def _preprocess(self, page_history_msg, db_history_msg):
        self._init_msgs(page_history_msg, db_history_msg)

        ## analysis msgs
        is_first_msg = db_history_msg is None
        has_system_msg = len(self._last_system_msgs) > 0
        user_msg_useless = len(self._last_user_msg) ==0
        if self._source is None:
            first_msg = self._msg_list[0]
            self._source = 'search'
            if first_msg['speaker']!='robot':
                self._source = 'user_ask'
        user_ask = self._source=='user_ask'

        cur_has_contact = False
        for parse_dict in self._last_parse_list:
            if 'contact' in parse_dict:
                cur_has_contact = True
                break
        chat_round = self._calc_chat_round()
        has_manual_touch = False
        for idx, cur in enumerate(self._msg_list):
            if cur['speaker']=='system' and '我已同意好友申请' in cur['msg']:
                if idx+1 < len(self._msg_list):
                    next_item = self._msg_list[idx+1]
                    if next_item['speaker']=='robot':
                        has_manual_touch = True
        return is_first_msg, has_system_msg, user_msg_useless, user_ask, chat_round, cur_has_contact, has_manual_touch