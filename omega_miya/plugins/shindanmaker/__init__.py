"""
@Author         : Ailitonia
@Date           : 2021/06/28 21:41
@FileName       : __init__.py.py
@Project        : nonebot2_miya 
@Description    : shindanmaker 无聊的占卜插件
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import datetime
from typing import Dict
from nonebot import on_command, export, logger
from nonebot.typing import T_State
from nonebot.adapters.cqhttp.bot import Bot
from nonebot.adapters.cqhttp.event import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.permission import GROUP
from omega_miya.utils.Omega_plugin_utils import init_export, init_permission_state, PluginCoolDown
from .data_source import ShindanMaker


# Custom plugin usage text
__plugin_name__ = 'ShindanMaker 占卜'
__plugin_usage__ = r'''【ShindanMaker 占卜】
使用ShindanMaker进行各种奇怪的占卜
只能在群里使用
就是要公开处刑！

**Permission**
Command & Lv.30
or AuthNode

**AuthNode**
basic

**CoolDown**
群组共享冷却时间
1 Minutes
用户冷却时间
1 Minutes

**Usage**
/ShindanMaker [占卜名称] [占卜对象名称]
/占卜 [占卜名称] [占卜对象名称]'''

# 声明本插件可配置的权限节点
__plugin_auth_node__ = [
    PluginCoolDown.skip_auth_node,
    'basic'
]

# 声明本插件的冷却时间配置
__plugin_cool_down__ = [
    PluginCoolDown(PluginCoolDown.user_type, 1),
    PluginCoolDown(PluginCoolDown.group_type, 1)
]

# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__, __plugin_auth_node__, __plugin_cool_down__)


# 缓存占卜名称与对应id
SHINDANMAKER_CACHE: Dict[str, int] = {}


# 注册事件响应器
shindan_maker = on_command(
    'ShindanMaker',
    # 使用run_preprocessor拦截权限管理, 在default_state初始化所需权限
    state=init_permission_state(
        name='shindan_maker',
        command=True,
        level=30,
        auth_node='basic'),
    aliases={'占卜', 'shindanmaker', 'SHINDANMAKER', 'Shindan', 'shindan', 'SHINDAN'},
    permission=GROUP,
    priority=20,
    block=True)


# 修改默认参数处理
@shindan_maker.args_parser
async def parse(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    if not args:
        await shindan_maker.reject('你似乎没有发送有效的参数呢QAQ, 请重新发送:')
    state[state["_current_key"]] = args[0]
    if state[state["_current_key"]] == '取消':
        await shindan_maker.finish('操作已取消')


@shindan_maker.handle()
async def handle_first_receive(bot: Bot, event: GroupMessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    state['id'] = 0
    if not args:
        pass
    elif args and len(args) == 1:
        state['shindan_name'] = args[0]
    elif args and len(args) == 2:
        state['shindan_name'] = args[0]
        state['input_name'] = args[1]
    else:
        await shindan_maker.finish('参数错误QAQ')

    # 特殊处理@人
    if len(event.message) >= 2:
        if event.message[1].type == 'at':
            at_qq = event.message[1].data.get('qq')
            group_member_list = await bot.get_group_member_list(group_id=event.group_id)
            nickname = [x for x in group_member_list if x.get('user_id') == int(at_qq)]
            if nickname:
                input_name = nickname[0].get('card') if nickname[0].get('card') else nickname[0].get('nickname')
                if input_name:
                    state['input_name'] = input_name


@shindan_maker.got('shindan_name', prompt='你想做什么占卜呢?\n不知道的话可以输入关键词进行搜索哦~')
async def handle_shindan_name(bot: Bot, event: GroupMessageEvent, state: T_State):
    global SHINDANMAKER_CACHE

    shindan_name = state['shindan_name']
    shindan_id = SHINDANMAKER_CACHE.get(shindan_name, 0)
    if shindan_id == 0:
        shindan_name_result = await ShindanMaker.search(keyword=shindan_name)
        if shindan_name_result.error:
            logger.error(f'User: {event.user_id} 获取 ShindanMaker 占卜信息失败, {shindan_name_result.info}')
            await shindan_maker.finish('获取ShindanMaker占卜信息失败了QAQ, 请稍后再试')
        else:
            for item in shindan_name_result.result:
                if item.get('name'):
                    SHINDANMAKER_CACHE.update({
                        item.get('name'): item.get('id', 0)
                    })
            shindan_id = SHINDANMAKER_CACHE.get(shindan_name, 0)
            if shindan_id == 0:
                shindan_list = '】\n【'.join([x.get('name') for x in shindan_name_result.result if x.get('name')])
                msg = f'已为你找到了以下占卜\n{"="*12}\n【{shindan_list}】\n{"="*12}\n' \
                      f'请输入您想要进行的占卜名称(方括号里面的完整名称):'
                await shindan_maker.reject(msg)

    state['id'] = shindan_id


@shindan_maker.got('input_name', prompt='请输入您想要进行占卜的人名:')
async def handle_input_name(bot: Bot, event: GroupMessageEvent, state: T_State):
    shindan_name = state['shindan_name']
    input_name = state['input_name']
    shindan_id = state['id']
    today = f"@{datetime.date.today().strftime('%Y%m%d')}@"
    # 加入日期使每天的结果不一样
    _input_name = f'{input_name}{today}'
    result = await ShindanMaker(maker_id=shindan_id).get_result(input_name=_input_name)
    if result.error:
        logger.error(f'User: {event.user_id} 获取 ShindanMaker 占卜结果失败, {result.info}')
        await shindan_maker.finish('获取ShindanMaker占卜结果失败了QAQ, 请稍后再试')

    result_text = result.result.replace(today, '')
    msg = f'{shindan_name}@{input_name}\n{"="*16}\n{result_text}'
    await shindan_maker.finish(msg)
