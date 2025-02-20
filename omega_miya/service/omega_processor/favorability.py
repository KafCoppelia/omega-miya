"""
@Author         : Ailitonia
@Date           : 2021/08/28 20:33
@FileName       : favorability.py
@Project        : nonebot2_miya 
@Description    : 好感度处理模块
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

from nonebot import logger
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent, PrivateMessageEvent

from omega_miya.database import EventEntityHelper
from omega_miya.result import BoolResult
from omega_miya.utils.process_utils import run_async_catching_exception


_log_prefix: str = '<lc>Friendship</lc> | '


async def postprocessor_friendship(bot: Bot, event: MessageEvent):
    """用户能量值及好感度处理"""
    friendship_incremental = 0.01 if isinstance(event, PrivateMessageEvent) else 1
    friendship_increase_result = await _add_user_friendship_energy(
        bot=bot, event=event, friendship_incremental=friendship_incremental,
        add_user_name=event.sender.nickname
    )

    if isinstance(friendship_increase_result, Exception):
        logger.opt(colors=True).error(
            f'{_log_prefix}Add User({event.user_id}) friendship energy failed with exception, '
            f'error: {friendship_increase_result}')
    elif friendship_increase_result.error:
        logger.opt(colors=True).error(
            f'{_log_prefix}Add User({event.user_id}) friendship energy failed, '
            f'database operation error: {friendship_increase_result.info}')
    else:
        logger.opt(colors=True).debug(
            f'{_log_prefix}Add User({event.user_id}) friendship energy success, energy increased')


@run_async_catching_exception
async def _add_user_friendship_energy(
        bot: Bot,
        event: MessageEvent,
        friendship_incremental: float,
        *,
        add_user_name: str = ''
) -> BoolResult:
    """为用户增加好感度, 若用户不存在则在数据库中初始化用户 Entity"""
    user = EventEntityHelper(bot=bot, event=event).get_event_user_entity()
    try:
        friendship_add_result = await user.add_friendship(energy=friendship_incremental)
    except Exception as e:
        logger.opt(colors=True).debug(f'{_log_prefix}Add User({user.tid}) friendship energy failed, {e}')
        add_user = await user.add_only(entity_name=add_user_name, related_entity_name=add_user_name)
        if add_user.success:
            logger.opt(colors=True).debug(f'{_log_prefix}Add and init User({user.tid}) succeed')
        else:
            logger.opt(colors=True).error(f'{_log_prefix}Add User({user.tid}) failed, {add_user.info}')
        friendship_add_result = await user.add_friendship(energy=friendship_incremental)
    return friendship_add_result


__all__ = [
    'postprocessor_friendship'
]
