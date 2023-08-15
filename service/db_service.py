from dao.task_dao import *
import json
from utils.utils import deal_json_invaild
from utils.utils import format_time
from datetime import datetime

def append_chat_msg(account_id, job_id, candidate_id, msg, init_history=False):
    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        logger.info(f'append_chat_msg abnormal chat not in db, will skip {account_id} {job_id} {candidate_id}')
        return
    _, db_history_msg, _ = candidate_info[0]
    if db_history_msg is None or db_history_msg =='None':
        if not init_history:
            return
        db_history_msg = []
    else:
        try:
            db_history_msg = json.loads(db_history_msg, strict=False)
        except BaseException as e:
            logger.info(f'db msg json parse abnormal, proc instead (e: {e}), (msg: {db_history_msg})')
            db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)

    db_history_msg.append({
        'speaker': 'robot',
        'msg': msg,
        'time': format_time(datetime.now())
    })

    details = json.dumps(db_history_msg, ensure_ascii=False)
    update_chat_only_details_db(account_id, job_id, candidate_id, details)
