import glob
import json
import re
from json import JSONDecodeError
from typing import Dict, OrderedDict

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from types import SimpleNamespace
from argparse import Namespace

import requests
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.absolute() / './.env')

from ruamel.yaml.scalarstring import LiteralScalarString
from ruamel.yaml.scalarstring import preserve_literal
from ruamel.yaml import YAML
from loguru import logger
import arrow

from toolkit.llm import Prompt, Vicuna, ChatGPT

base_path = None
domain_path = None


class Context(SimpleNamespace):
    nlu: pd.DataFrame
    args: Namespace
    domain: str
    domain_path: Path
    annotated_example_path: Path
    unannotated_example_path: Path
    rasa_yml_version: str


def fetch_data(dbname, sql):
    headers = {
        'Cookie': os.getenv('COOKIE_STR')
    }

    r = requests.post(
        'https://gis-app.corp.bianlifeng.com/hire/custom_get_data/v1', json={
            'dbname': dbname,
            'sql': sql
        },
        headers=headers
    )

    return json.loads(r.text).get('data')


def read_yaml(path):
    with open(domain_path / path, 'r', encoding='utf-8') as f:
        yaml = YAML()
        return yaml.load(f.read())


def to_yaml(path, obj):
    p = domain_path / path
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        yaml = YAML()
        yaml.dump(obj, f)


def command_build(context):
    """
    根据 nlu.xlsx 生成对应的配置文件
    :return:
    """

    command_build_nlu_yml(context)
    command_build_domain_yml(context)
    command_build_data_responses_yml(context)
    command_build_data_stories_yml(context)
    command_build_data_rules_yml(context)
    command_build_nlu_xlsx_yml(context)


def command_build_nlu_yml(context):
    """
    1. 生成 nlu.yml
    2. 生成 rasa_deploy/nlu_data/{intent}.yml - 其中的 annotated_example.csv 是已经打过标的数据。
        example可能的来源
            - 数据库
            - excel 文件
    :param context:

    :return:
    """
    # 1
    to_yaml('rasa_deploy/data/nlu.yml', read_yaml('rasa_conf/nlu.yml'))

    # 2 
    intents = []
    for i, row in context.nlu.iterrows():
        if pd.isna(row['intent_cn']):
            continue

        # 使用了所有 nlu 的 example
        examples = [example.strip() for example in row['examples'].split('\n') if example.strip() != '']
        # 再加上 annotated_example
        if context.annotated_example_path.exists():
            ae = pd.read_csv(context.annotated_example_path)
            examples.extend([example.strip() for example in ae[ae['intent'] == row['intent_cn']]['example'].tolist() if example.strip() != ''])

        # 处理掉examples所有中间的空格
        examples = [re.sub(r'\s+', '，', example) for example in examples]

        intents.append({
            'intent': row['intent_cn'],
            'examples': LiteralScalarString("- " + "\n- ".join(examples))
        })

        nlu_obj = {
            'version': context.rasa_yml_version,
            'nlu': [
                {
                    'intent': row['intent_cn'],
                    'examples': LiteralScalarString("- " + "\n- ".join(examples))
                }
            ]
        }
        to_yaml(f"rasa_deploy/data/nlu_data/{row['intent_cn']}.yml", nlu_obj)

    # 3，不再单独写入 nlu_data，把所有 intent 配置写入 nlu.yml
    # nlu_obj = read_yaml('rasa_conf/nlu.yml')
    # nlu_obj['nlu'] = intents
    # to_yaml('rasa_deploy/data/nlu.yml', nlu_obj)


def command_build_domain_yml(context):
    """
    生成 domain.yml
    :param context:
    :return:
    """
    domain_dict = read_yaml('rasa_conf/domain.yml')
    domain_dict['intents'] = context.nlu['intent_cn'].tolist()
    obj = {k: v for k, v in domain_dict.items() if v is not None}

    to_yaml('rasa_deploy/domain.yml', obj)


def command_build_data_responses_yml(context):
    """
    这里来定义简单回复
    :param context:
    :return:
    """
    # responses = {}
    # for intent_cn in context.nlu['intent_cn'].tolist():
    #     responses[f'utter_{intent_cn}'] = [{'action': 'action_utter_intent_prompt'}]
    obj = {
        'responses': {},
        'version': context.rasa_yml_version
    }

    to_yaml('rasa_deploy/data/responses.yml', obj)


def command_build_data_rules_yml(context):
    """
    用来生成 rules.yml

    rules.yml 文件中的规则则是用来处理这些确定性的对话逻辑的。规则是硬编码的，意味着只要规则的前提条件满足，那么规则就会被触发，不受机器学习模型的影响。因此，对于一些预设的、确定性的对话逻辑，比如某个意图触发后执行某个action，或者在某种条件下执行某个action等，规则是非常适合的。

    至于优先级，规则的优先级高于故事。也就是说，当一个对话的状态既满足一个规则的前提条件，又符合一个故事的对话模式时，Rasa 会优先执行规则。如果一个对话的状态既不满足任何规则的前提条件，又不符合任何故事的对话模式，那么Rasa会根据机器学习模型的预测结果来决定下一步的行为。

    :param context:
    :return:
    """
    rules_obj = read_yaml('rasa_conf/rules.yml')

    used_intents = set()
    for rule in rules_obj.get('rules'):
        for step in rule.get('steps'):
            if step.get('intent'):
                used_intents.add(step['intent'])
            if step.get('or'):
                for or_step in step.get('or'):
                    if or_step.get('intent'):
                        used_intents.add(or_step['intent'])

    for intent_cn in context.nlu['intent_cn'].tolist():
        if intent_cn not in used_intents:
            rules_obj['rules'].append({
                'rule': f'{intent_cn}',
                'steps': [
                    {
                        'intent': f'{intent_cn}',
                    }, {
                        'action': f'action_utter_intent_prompt'
                    }
                ]
            })

    to_yaml('rasa_deploy/data/rules.yml', rules_obj)


def command_build_data_stories_yml(context):
    """
    将所有 intent 描述到一个 story 中

    stories.yml 文件中的故事是一种描述对话流程的方式，它可以捕获更复杂的对话模式和长期的对话上下文。然而，由于它们依赖于机器学习的模型，因此对于某些特定的、确定性的对话逻辑，它们可能无法保证始终给出正确的预测。

    :param context: 
    :return: 
    """

    # version: "3.0"
    # stories:
    # - story: happy path
    #   steps:
    #   - intent: greet
    #   - action: utter_greet
    #   - intent: mood_great
    #   - action: utter_happy

    stories_obj = read_yaml('rasa_conf/stories.yml')
    # story_obj = {
    #     'story': 'intent to prompt',
    #     'steps': [
    #     ]
    # }
    # for intent_cn in context.nlu['intent_cn'].tolist():
    #     story_obj['steps'].append({
    #         'intent': f'{intent_cn}'
    #     })
    # story_obj['steps'].append(
    #     {
    #         'action': 'action_utter_intent_prompt'
    #     })
    # stories_obj['stories'].append(story_obj)

    to_yaml('rasa_deploy/data/stories.yml', stories_obj)


def command_build_nlu_xlsx_yml(context):
    """
    创建 intent -> answer 的标准答案 kv file
    :return:
    """
    obj = {}
    for i, row in context.nlu.iterrows():
        obj[row['intent_cn']] = row.to_dict()
    to_yaml('rasa_deploy/data/answer.yml', obj)


def command_example(context):
    pass


def command_annotate(context):
    """
    根据 type 进行打标文件的创建
    :param context:
    :return:
    """

    assert context.args.annotate in ['llm', 'manual'], '请指定打标类型. llm / manual'

    if context.args.annotate == 'llm':
        command_annotate_llm(context)
    elif context.args.annotate == 'manual':
        command_annotate_manual(context)


def generate_corpus(item):
    entities = item.get('entities')
    entities_dict = {}
    for e in entities:
        # TODO: change location to e['entities']
        entities_dict[e['start']] = [e['end'], 'location']
    entities_list = sorted(entities_dict.items(), key=lambda s: s[0])

    tmp = ''
    sstart = 0
    eend = 0
    last_end = 0
    error = False
    for ee in entities_list:
        if ee[0] < last_end:
            error = True
        eend = ee[0]
        tmp += item['text'][sstart:eend]
        tmp += f"[{item['text'][ee[0]:ee[1][0]]}]"
        tmp += f"({ee[1][1]})"
        sstart = ee[1][0]
        last_end = ee[1][0]

    tmp += item['text'][sstart:]
    return tmp


def command_annotate_manual(context):
    """
    人工打标
    1. 要指定一个目录 args.json_path
    2. 会寻找此目录下，所有打标平台输出的json文件
    3. 批量转为 annotated_example.csv 格式，并加上日期戳
    :param context:
    :return:
    """
    examples = []
    for f in glob.glob(f'{context.args.json_path}/**/*.json', recursive=True):
        logger.info(f'正在处理 {f}')
        try:
            json_str = open(f).read()
            obj = json.loads(json_str)
        except JSONDecodeError:
            json_str = open(f, 'r', encoding='utf-8-sig').read()
            obj = json.loads(json_str)
        json_examples = obj.get('rasa_nlu_data').get('common_examples')
        for item in json_examples:
            if item.get('text', '') != '' and item.get('intent', '') != '':
                examples.append({
                    'intent': item.get('intent'),
                    'example': generate_corpus(item),
                    'source-type': 'manual',
                    'source-file': f.replace(context.args.json_path, '')
                })
    df = pd.DataFrame(examples)
    df = df.sort_values(by=['intent'])
    df_drop_duplicates = df.drop_duplicates(subset='example')

    def save_csv(df, content=None):
        today = arrow.now().format('YYYYMMDD')
        if content is None:
            output_csv_path = domain_path / f'annotated_example.csv'
        else:
            output_csv_path = domain_path / f'annotated_example-{today}-{content}.csv'
        df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        logger.info(f'已生成 {output_csv_path}')

    # 原始标注数据
    save_csv(df_drop_duplicates)

    # 质检-未知
    def top_N_examples(group):
        return group.sort_values('example', key=lambda x: x.str.len(), ascending=False).head(20)

    dfx = df_drop_duplicates[df_drop_duplicates['intent'] == '未知'].copy()
    dfx['修正意图'] = ''
    dfx['补充意图答案'] = ''
    save_csv(dfx, '质检-未知')

    # 质检-非未知抽样
    dfx = df_drop_duplicates[df_drop_duplicates['intent'] != '未知'].copy()
    dfx['修正意图'] = ''
    dfx['补充意图答案'] = ''
    dfx = dfx.groupby('intent').apply(top_N_examples).reset_index(drop=True)
    save_csv(dfx, '质检抽样-非未知')


def command_annotate_llm(context):
    """
    自动标注
    根据nlu.xlsx中的`intent_cn`，为 `unannotated_example.csv` 中进行自动标注
    标注后保存到`annotated_example_by_llm.csv`，文件字段为 [`intent`, `example`]
    :param context:
    :return:
    """

    # 已经标注过的内容
    annotated_example: OrderedDict[str, Dict] = OrderedDict[str, Dict]()
    try:
        df = pd.read_csv(context.domain_path / 'annotated_example_by_llm.csv')
        for index, row in df.iterrows():
            annotated_example[row['example']] = row.to_dict()
    except:
        pass

    # 还没有标注过的内容
    unannotated_example_df = pd.read_csv(context.domain_path / 'unannotated_example.csv')
    unannotated_example_df = unannotated_example_df[
        ~unannotated_example_df['example'].isin(annotated_example.keys())].copy()

    def annoted(examples, intent_key, intent_examples, show_prompt=False):
        ndf = context.nlu
        answer = ndf[ndf['intent_cn'] == intent_key].iloc[0]['answer']
        prompt = Prompt()
        prompt.add_system_message(f"""
你是一个AI文本标注员，负责判断`句子`与`意图`的相关性，选择出所有意图中最相关的。

判断的规则为： 
* `意图的答案`中能够找到`句子`的问题，且逻辑合理，就是相关


`意图`为: 
* 询问入职流程
* 询问入职要求
* 询问工作相关
* 询问门店基本情况
* 询问店长岗位
* 询问薪资相关
* 询问福利相关
* 询问健康证办理方式
* 询问培训相关
* 询问离职流程
* 打招呼
* 希望人工聊天
* 询问此岗位不相关的概念
* 询问人事其它业务
* 询问信息泄漏


输出格式为csv:
```
句子,意图
```

比如:
句子是`好的，去医院或者社区都可以对吗`，意图是`询问健康证办理方式`
输出就是:
```
句子,意图
好的，去医院或者社区都可以对吗,询问健康证办理方式
```

输出要求:
* 简洁！不要`输出格式`以外的内容！ 
* 只输出一个意图结果！
* 如果所有意图都不相关，请写“未知”
        """)
        #         prompt.add_system_message(f"""
        # 你是一个AI文本标注员，负责判断`句子`与`意图`的相关性。
        # 判断的规则为：
        # * `意图的答案`中能够找到`句子`的问题，且逻辑合理，就是相关
        #
        #
        # `意图`为:`{intent_key}`
        #
        # `意图的内容`为:
        # ```
        # {answer}
        # ```
        #
        # 与`意图`相关的例子:
        # {intent_examples}
        #
        # 输出格式:
        # ```
        # result: 相关 或 不相关
        # reason: ""
        # ```
        #
        # 输出要求:
        # * 简洁！不要`输出格式`以外的内容！
        #         """)
        str_example = '\n- '.join(examples)
        prompt.add_user_message(f"`句子`为{len(examples)}条记录: \n{str_example}")

        if show_prompt:
            logger.info(prompt.to_string())

        result = ChatGPT().chat(prompt)
        logger.info(f'自动标注结果: \n{result}')
        if result == 'True':
            return True
        else:
            return False

    for index, row in context.nlu.iterrows():
        intent_name = row['intent_cn']
        intent_examples = row['examples']
        if intent_name not in ['询问入职要求']:
            continue
        examples = unannotated_example_df['example'].tolist()
        N = 10
        for i in range(0, len(examples), N):
            result = annoted(examples[i:i + N], intent_name, intent_examples, show_prompt=i == 0)

            import time
            time.sleep(20)


def command_doccano(context):
    """

    :param context: tag - 根据nlu.xlsx生成标签 / 
    :return:
    """

    if context.args.doccano == 'tag':
        command_doccano_tag(context)
    elif context.args.doccano == 'dataset':
        command_doccano_dataset(context)
    else:
        logger.error('doccano 未知参数')


def command_doccano_tag(context):
    import seaborn as sns
    import numpy as np
    results = []
    np.random.seed(42)
    colors = sns.color_palette(n_colors=50).as_hex()
    i = 0
    for type_name, group in context.nlu.groupby('type'):
        i += 1
        color = colors[i]
        for i, row in group.iterrows():
            r = {
                'text': row['intent_cn'],
                'suffix_key': '',
                'text_color': '#ffffff',
                'background_color': color
            }
            results.append(r)
    fname = context.domain_path / 'doccano-tag.json'
    with open(fname, 'w+') as f:
        f.write(json.dumps(results, ensure_ascii=False))
        logger.info(f'已生成 doccano tag file: {fname}')


def command_doccano_dataset(context):
    """
    1. 拿到wechat的数据
    2. 清洗数据
    3. 格式化为doccano格式
    :param context:
    :return:
    """

    # part1
    sql = """
        select
            id ,  
            message_data , 
            create_time 
        from wechat_message
        where sender_type = 0 
        and message_type = 'text'
        order by create_time desc 
        limit 5000
    """
    data = fetch_data('gishire', sql)
    logger.info(f'已加载 {len(data)} 条数据')

    # part2 
    df = pd.DataFrame(data)

    # --  message 中的内容是，`{"content":"我在秦皇岛"}`，将 content 的内容取出来
    df['content'] = df['message_data'].apply(lambda x: json.loads(x)['content'])

    # --  将 content 的内容 strip， 然后将中间的空格（无论多少个）转为1个中文逗号
    df['content'] = df['content'].apply(lambda x: x.strip().replace(' ', '，'))

    # --  重复的 content 去重
    df = df.drop_duplicates('content')

    logger.info(f'已处理 {len(df)} 条数据')

    # part3 
    # -- 将每一行转为 List[str] 类型，其中的 str 格式为
    # { "text": df['content'] }
    results = []
    for i, row in df.iterrows():
        r = {
            'text': row['content'],
        }
        results.append(json.dumps(r, ensure_ascii=False))
    fname = context.domain_path / 'doccano-dataset.jsonl'
    with open(fname, 'w+') as f:
        f.write('\n'.join(results))
        logger.info(f'已生成 doccano dataset file: {fname}')


def check_nlu_df(nlu_df):
    assert 'type' in nlu_df.columns, 'nlu.xlsx中必须包含type列.'
    assert 'intent_cn' in nlu_df.columns, 'nlu.xlsx中必须包含intent_cn列.'
    assert 'examples' in nlu_df.columns, 'nlu.xlsx中必须包含examples列.'
    assert 'answer' in nlu_df.columns, 'nlu.xlsx中必须包含answer列.'

    assert len(nlu_df['intent_cn'].tolist()) == len(set(nlu_df['intent_cn'].tolist())), 'intent_cn字段必须唯一.'
    assert not (nlu_df['examples'].str.strip() == '').any(), 'examples字段不能为空字符串.'
    assert not (nlu_df['answer'].str.strip() == '').any(), 'answer字段不能为空字符串.'


def command_draft(context):
    """
    草稿模式
    :param context:
    :return:
    """
    examples = []
    for f in glob.glob(str(context.domain_path / '*.csv')):
        if '质检' in f:
            continue
        df = pd.read_csv(f)
        examples.extend(df['example'].tolist())

    dfx = pd.DataFrame(data={
        'example': list(set(examples))
    })
    dfx['example'] = dfx['example'].str.strip()
    dfx = dfx.replace('', np.nan)
    dfx = dfx.dropna()
    dfx.to_csv(context.domain_path / 'unannotated_example.csv', index=False, encoding='utf-8-sig')


def main():
    global base_path
    global domain_path

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('domain', help='domain的名称')
    parser.add_argument('--build', help='生成指定domain的配置文件', action='store_true')
    parser.add_argument('--example',
                        help='根据nlu.xlsx，使用chatgpt生成样例句子，保存在annotated_example.csv。 请指定生成的数量。 ',
                        type=int)
    parser.add_argument('--annotate',
                        help='标注：方式1、可以将人工打标的JSON自动导出为annotated_example.csv。 方式2、unannotated_example.csv中未标注的句子，根据nlu.xlsx，使用chatgpt自动标注',
                        type=str)
    parser.add_argument('--json_path', help='annotate为方式1时必须指定json_path', type=str)
    parser.add_argument('--doccano', help='doccano相关工具', type=str)

    parser.add_argument('--draft', help='draft模式', action='store_true')

    args = parser.parse_args()
    base_path = Path(__file__).parent.parent.absolute()

    assert args.domain, 'domain必须指定.'

    domain = args.domain
    domain_path = base_path / 'domains' / domain

    assert domain_path.exists(), f'{domain_path} 必须存在.'

    nlu_filepath = domain_path / 'nlu.xlsx'

    assert nlu_filepath.exists(), f'{nlu_filepath} 必须存在.'

    nlu_df = pd.read_excel(nlu_filepath).dropna()

    check_nlu_df(nlu_df)

    context = Context(**{
        'nlu': nlu_df,
        'args': args,
        'domain': domain,
        'domain_path': domain_path,
        'annotated_example_path': domain_path / 'annotated_example.csv',
        'unannotated_example_path': domain_path / 'unannotated_example.csv',
        'rasa_yml_version': '3.0'
    })

    if args.build:
        command_build(context=context)
    elif args.example:
        command_example(context=context)
    elif args.annotate:
        command_annotate(context=context)
    elif args.doccano:
        command_doccano(context=context)
    elif args.draft:
        command_draft(context=context)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
