from service.tools_service import search_profile_by_tag
from algo.llm_inference import gpt_manager
from algo.llm_base_model import Prompt
import xlsxwriter
import traceback

def data_to_excel_file(file_path, titles, data):
    try:
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        title_formatter = workbook.add_format()
        title_formatter.set_border(1)
        title_formatter.set_bg_color('#cccccc')
        title_formatter.set_align('center')
        title_formatter.set_bold()

        row_formatter = workbook.add_format()
        row_formatter.set_text_wrap(True)
        worksheet.set_column(8,8, 60, row_formatter)
        worksheet.write_row('A1', titles, title_formatter)
        count = 2

        for row in data:
            worksheet.write_row('A{}'.format(count), row, row_formatter)
            count += 1
    except BaseException as e:
        print("[backend_tools] data to excel error {}", e)
        print(traceback.format_exc())
    finally:
        workbook.close()

def get_stability(detail):
    if 'last5Jump' not in detail or detail['last5Jump'] is None:
        return '不确定'
    last_5_jump = detail['last5Jump']
    if last_5_jump <= 1:
        return '高'
    elif last_5_jump <= 3:
        return '中'
    else:
        return '低'
def get_hr_attribute(hr_cv_str):
    prompt_msg = '你是一个资深简历分析专家, 给你一个HR简历, 请回候选人的职位是:\nHRBP,COE还是SSC\n, 如果不能确定请回答"不确定", 简历如下\n$$$\n' + hr_cv_str[0:3500] + "\n$$$"
    prompt = Prompt()
    prompt.add_user_message(prompt_msg)
    output = gpt_manager.chat_task(prompt)
    return output

def get_hr_module(hr_cv_str):
    prompt_msg = '你是一个资深简历分析专家, 给你一个HR简历, 请回候选人的负责职能是 候选项是:\n薪酬,招聘, 员工关系, 组织文化, 培训,绩效\n 可以多选, 如果不能确定请回答"不确定", 简历如下\n$$$\n' + hr_cv_str[0:3500] + "\n$$$"
    prompt = Prompt()
    prompt.add_user_message(prompt_msg)
    output = gpt_manager.chat_task(prompt)
    return output

def get_hr_level(hr_cv_str):
    prompt_msg = '你是一个资深简历分析专家, 给你一个HR简历, 请回候选人的层级是:\n经理,总监, HRVP\n 如果不能确定请回答"不确定", 简历如下\n$$$\n' + hr_cv_str[0:3500] + "\n$$$"
    prompt = Prompt()
    prompt.add_user_message(prompt_msg)
    output = gpt_manager.chat_task(prompt)
    return output

def main():
    manage_account_id = '18870243977@163.com'
    platform = 'Linkedin'
    tags = ['菲律宾HR']
    page = 1
    limit = 300
    contact2str = True
    data, error_msg = search_profile_by_tag(manage_account_id, platform, tags, page, limit, contact2str)
    if error_msg is not None:
        print(f'{error_msg}')
        exit(1)
    details = data['details']
    print(f'get {len(details)} of candidates, {manage_account_id}-{tags} ')
    titles = ['候选人id', '年龄', '语言', '稳定性', '职位', '职能属性', '层级', '简历']
    data  = []
    for detail in details:
        row = []
        print(detail)
        if 'candidateId' not in detail:
            continue
        row.append(detail['candidateId'])
        row.append(str(detail['age']) if 'age' in detail and detail['age'] is not None else '不确定')
        row.append(str(detail['language']) if 'language' in detail and detail['language'] is not None else '不确定')
        row.append(str(get_stability(detail)))
        cv = detail['cv']
        if cv is None:
            row.append('不确定')
            row.append('不确定')
            row.append('不确定')
            row.append('无')
        else:
            row.append(str(get_hr_attribute(cv)))
            row.append(str(get_hr_module(cv)))
            row.append(str(get_hr_level(cv)))
            row.append(detail['cv'])
        data.append(row)
    data_to_excel_file('/root/f.xlsx', titles, data)


if __name__ == '__main__':
    main()