from dao.tool_dao import *
from service.tools_service import *
import zipfile
from utils.utils import filter_task_exec_cache
import urllib
def schedule_filter_task_exec():
    task_res = get_undo_filter_task()
    logger.info(f"exec_filter_task, task_sum:{len(task_res)}")
    for t in task_res:
        logger.info(f"exec_filter_task_start: task_id:{t[0]}, manage_id:{t[1]}")
        update_filter_task_status(1, int(t[0]))
        zip_url = t[3]
        flag, zip_file_path, zip_file_name = downloadFile(zip_url)
        if not flag:
            update_filter_task_status(-1, int(t[0]))
            update_filter_result('[]', int(t[0]))
            continue
        os.chdir(file_path_prefix)
        os.system(f'unzip {zip_file_name}')
        file_raw_list = os.listdir('./')
        # f = zipfile.ZipFile(zip_file_path ,'r')
        file_list = []
        for f_name in file_raw_list:
            if f_name.endswith('jpg') or f_name.endswith('jpeg') or f_name.endswith('png') or f_name.endswith('doc') or f_name.endswith('docx') or f_name.endswith('pdf'):
                if '/' in f_name:
                    continue
                # f.extract(f_name, file_path_prefix)
                # try:
                #     file_name_process = f_name.encode('cp437').decode('gbk')
                # except:
                #     file_name_process = f_name.encode('utf-8').decode('utf-8')
                # os.rename(file_path_prefix + f_name, file_path_prefix + file_name_process)
                file_list.append(file_path_prefix + f_name)
            else:
                if os.path.isdir(file_path_prefix + f_name):
                    os.system(f'rm -rf {file_path_prefix + f_name}')
                else:
                    os.remove(file_path_prefix + f_name)
        logger.info(f"exec_filter_task_f_name_list:{len(file_list)} {file_list}")
        filter_task_exec_cache[zip_url] = float(len(file_list) * 40) / 60
        filter_result = exec_filter_task(t[1], file_list, t[2])
        update_filter_task_status(2, int(t[0]))
        update_filter_result(json.dumps(filter_result, ensure_ascii=False), int(t[0]))
        for f in file_list:
            os.remove(f)
        os.remove(zip_file_path)
        logger.info(f"exec_filter_task_end: task_id:{t[0]}, manage_id:{t[1]}, file_list:{file_list}")