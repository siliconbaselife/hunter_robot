from dao.tool_dao import *
from service.tools_service import *
import zipfile

def schedule_filter_task_exec():
    task_res = get_undo_filter_task()
    logger.info(f"exec_filter_task, task_sum:{len(task_res)}")
    for t in task_res:
        logger.info(f"exec_filter_task_start: task_id:{t[0]}, manage_id:{t[1]}")
        update_filter_task_status(1, int(t[0]))
        zip_url = t[3]
        flag, file_path = downloadFile(zip_url)
        if not flag:
            update_filter_task_status(-1, int(t[0]))
            update_filter_result()
            continue
        f = zipfile.ZipFile(file_path ,'r')
        file_list = []
        for f_name in f.namelist():
            if f_name.endswith('jpg') or f_name.endswith('jpeg') or f_name.endswith('png') or f_name.endswith('doc') or f_name.endswith('docx') or f_name.endswith('pdf'):
                if '/' in f_name:
                    continue
                f.extract(f_name, file_path_prefix)
                file_list.append(file_path_prefix + f_name)
        logger.info(f"exec_filter_task_f_name_list: {file_list}")
        exec_filter_task(t[1], file_list, t[2])
        update_filter_task_status(2, int(t[0]))
        for f in file_list:
            os.remove(f)
        logger.info(f"exec_filter_task_end: task_id:{t[0]}, manage_id:{t[1]}, file_list:{file_list}")