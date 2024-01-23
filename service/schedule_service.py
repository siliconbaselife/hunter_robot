from dao.tool_dao import *
from service.tools_service import *
from utils.utils import filter_task_exec_cache, ensure_dir, recursive_find_files
import urllib
from os.path import join, basename, isdir
import shutil


def schedule_filter_task_exec():
    task_res = get_undo_filter_task()
    logger.info(f"exec_filter_task, task_sum:{len(task_res)}")
    support_extension = ['.jpeg', '.png', '.doc', '.docx', '.pdf']
    for t in task_res:
        task_id_str = str(t[0])
        logger.info(f"exec_filter_task_start: task_id:{task_id_str}, manage_id:{t[1]}")
        update_filter_task_status(1, int(t[0]))
        zip_url = t[3]
        zip_file_path = download_file(zip_url)
        if not zip_file_path:
            update_filter_task_status(-1, int(t[0]))
            update_filter_result('[]', '[]', int(t[0]))
            continue
        # os.chdir(file_path_prefix)
        unzip_dir = join(file_path_prefix, task_id_str)
        ensure_dir(unzip_dir, clear_existing=True)
        # shutil or zipfile lib chinese file name mess code
        os.system(f'unzip {zip_file_path} -d {unzip_dir}')
        extract_files = recursive_find_files(unzip_dir, contains=support_extension)
        # os.system(f'unzip {zip_file_name}')
        # file_raw_list = os.listdir('./')
        # f = zipfile.ZipFile(zip_file_path ,'r')
        # for f_name in exec_filter_task:
        #     if f_name.endswith('jpg') or f_name.endswith('jpeg') or f_name.endswith('png') or f_name.endswith('doc') or f_name.endswith('docx') or f_name.endswith('pdf'):
        #         if '/' in f_name:
        #             continue
        #         # f.extract(f_name, file_path_prefix)
        #         # try:
        #         #     file_name_process = f_name.encode('cp437').decode('gbk')
        #         # except:
        #         #     file_name_process = f_name.encode('utf-8').decode('utf-8')
        #         # os.rename(file_path_prefix + f_name, file_path_prefix + file_name_process)
        #         file_list.append(file_path_prefix + f_name)
        #     else:
        #         if os.path.isdir(file_path_prefix + f_name):
        #             os.system(f'rm -rf {file_path_prefix + f_name}')
        #         else:
        #             os.remove(file_path_prefix + f_name)
        logger.info(f"exec_filter_task_f_name_list:{len(extract_files)} {extract_files}")
        filter_task_exec_cache[zip_url] = float(len(extract_files) * 40) / 60
        filter_result, format_resume_info = exec_filter_task(t[1], extract_files, t[2])
        update_filter_task_status(2, int(t[0]))
        update_filter_result(json.dumps(filter_result, ensure_ascii=False), json.dumps(format_resume_info, ensure_ascii=False), int(t[0]))
        shutil.rmtree(unzip_dir)
        os.remove(zip_file_path)
        logger.info(f"exec_filter_task_end: task_id:{t[0]}, manage_id:{t[1]}, file_list:{extract_files}")