"""
Executor Capability Registration Service
执行器能力注册服务 - 启动时向后端注册自己的能力
"""
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)


class CapabilityRegistrationService:
    """执行器能力注册服务"""

    def __init__(self, backend_url: str, executor_id: str, executor_version: str):
        self.backend_url = backend_url.rstrip('/')
        self.executor_id = executor_id
        self.executor_version = executor_version
        self.client = None
        self._heartbeat_task = None
        self._is_running = False

    async def start(self):
        """启动注册服务"""
        self._is_running = True
        self.client = httpx.AsyncClient(timeout=30.0)

        # 启动时注册一次
        await self._register_capabilities()

        # 启动心跳任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(f"能力注册服务已启动: {self.executor_id}")

    async def stop(self):
        """停止注册服务"""
        self._is_running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.client:
            await self.client.aclose()

        logger.info(f"能力注册服务已停止: {self.executor_id}")

    async def _register_capabilities(self):
        """注册执行器能力"""
        try:
            # 收集执行器支持的所有操作类型
            capabilities = self._collect_capabilities()

            payload = {
                "executor_id": self.executor_id,
                "executor_version": self.executor_version,
                "hostname": self._get_hostname(),
                "ip_address": self._get_ip_address(),
                "capabilities": capabilities
            }

            logger.info(f"注册数据: {payload}")

            url = f"{self.backend_url}/api/v1/executor-capabilities/register"
            response = await self.client.post(url, json=payload)

            # 打印响应内容用于调试
            logger.info(f"注册响应状态: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"注册响应内容: {response.text}")

            response.raise_for_status()

            result = response.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                logger.info(
                    f"执行器注册成功: {data.get('new_actions_count')} 个新操作, "
                    f"总共 {data.get('total_actions_count')} 个操作"
                )
            else:
                logger.error(f"注册失败: {result.get('message')}")

        except httpx.HTTPError as e:
            logger.error(f"注册请求失败: {e}")
        except Exception as e:
            logger.error(f"注册失败: {e}", exc_info=True)

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._is_running:
            try:
                await asyncio.sleep(settings.heartbeat_interval)

                payload = {
                    "executor_id": self.executor_id,
                    "executor_version": self.executor_version
                }

                url = f"{self.backend_url}/api/v1/executor-capabilities/heartbeat"
                response = await self.client.post(url, json=payload)

                if response.status_code == 200:
                    logger.debug(f"心跳成功: {self.executor_id}")
                else:
                    logger.warning(f"心跳失败: {response.status_code}")

            except Exception as e:
                logger.error(f"心跳失败: {e}")

    def _collect_capabilities(self) -> List[Dict[str, Any]]:
        """
        收集执行器支持的操作类型

        这里是执行器插件化的核心：
        - 扫描内置操作处理器
        - 扫描插件目录
        - 返回统一的操作定义
        """
        from ..core.step_executor import StepExecutor

        capabilities = []

        # 内置操作类型定义
        builtin_actions = {
            # ========== 基础操作 ==========
            'click': {
                'display_name': '点击',
                'category': '基础操作',
                'description': '点击屏幕元素',
                'color': 'blue',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '直接点击定位到的元素',
            },
            'long_press': {
                'display_name': '长按',
                'category': '基础操作',
                'description': '长按屏幕元素（默认2秒）',
                'color': 'cyan',
                'requires_element': True,
                'requires_value': False,
                'value_format': '持续时间（秒）可选',
                'value_example': '3',
                'value_description': '可选参数，长按持续时间（秒），默认2秒',
            },
            'input': {
                'display_name': '输入',
                'category': '基础操作',
                'description': '输入文本到元素',
                'color': 'green',
                'requires_element': True,
                'requires_value': True,
                'value_format': '文本内容',
                'value_example': 'hello world',
                'value_description': '要输入的文本内容，支持变量如 ${username}',
            },
            'clear_text': {
                'display_name': '清除文本',
                'category': '基础操作',
                'description': '清除元素文本内容',
                'color': 'lime',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '清空输入框中的所有文本',
            },
            'swipe': {
                'display_name': '滑动',
                'category': '基础操作',
                'description': '在屏幕上滑动',
                'color': 'purple',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'x1,y1,x2,y2,duration',
                'value_example': '500,1000,500,500,500',
                'value_description': '起点坐标(x1,y1), 终点坐标(x2,y2), 持续时间(毫秒)',
            },
            'hardware_back': {
                'display_name': '返回键',
                'category': '基础操作',
                'description': '按返回键',
                'color': 'default',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '模拟按下Android返回键',
            },
            'hardware_home': {
                'display_name': 'Home键',
                'category': '基础操作',
                'description': '按Home键',
                'color': 'default',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '模拟按下Android Home键',
            },
            'hardware_recent': {
                'display_name': '最近任务键',
                'category': '基础操作',
                'description': '按最近任务键',
                'color': 'default',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '模拟按下Android最近任务键',
            },

            # ========== 等待操作 ==========
            'wait_element': {
                'display_name': '等待元素',
                'category': '等待',
                'description': '等待元素出现（默认10秒超时）',
                'color': 'orange',
                'requires_element': True,
                'requires_value': False,
                'value_format': '超时时间（秒）可选',
                'value_example': '30',
                'value_description': '可选参数，等待超时时间（秒），默认10秒',
            },
            'wait_time': {
                'display_name': '等待时间',
                'category': '等待',
                'description': '等待指定时间',
                'color': 'orange',
                'requires_element': False,
                'requires_value': True,
                'value_format': '秒数',
                'value_example': '5',
                'value_description': '等待的秒数，支持小数如0.5表示500毫秒',
            },
            'wait_until': {
                'display_name': '等待直到',
                'category': '等待',
                'description': '等待直到条件满足',
                'color': 'orange',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'condition:value,timeout',
                'value_example': 'text:登录成功,30',
                'value_description': '条件类型:期望值,超时秒数。支持text/exists/enabled等条件',
            },

            # ========== 断言操作 ==========
            'assert_text': {
                'display_name': '断言文本',
                'category': '断言',
                'description': '断言元素包含指定文本',
                'color': 'red',
                'requires_element': True,
                'requires_value': True,
                'value_format': '期望文本',
                'value_example': '登录成功',
                'value_description': '期望元素包含的文本内容',
            },
            'assert_exists': {
                'display_name': '断言存在',
                'category': '断言',
                'description': '断言元素存在',
                'color': 'magenta',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '断言元素存在于页面中',
            },
            'assert_not_exists': {
                'display_name': '断言不存在',
                'category': '断言',
                'description': '断言元素不存在',
                'color': 'volcano',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '断言元素不存在于页面中',
            },
            'assert_color': {
                'display_name': '断言颜色',
                'category': '断言',
                'description': '断言元素颜色',
                'color': 'red',
                'requires_element': True,
                'requires_value': True,
                'value_format': '颜色值',
                'value_example': '#FF0000',
                'value_description': '期望的颜色值（十六进制）',
            },
            'assert_enabled': {
                'display_name': '断言可用',
                'category': '断言',
                'description': '断言元素可用',
                'color': 'red',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '断言元素处于可用状态（未禁用）',
            },
            'assert_visible': {
                'display_name': '断言可见',
                'category': '断言',
                'description': '断言元素可见',
                'color': 'red',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '断言元素在屏幕上可见',
            },

            # ========== 变量提取操作 ⭐ ==========
            'extract_text': {
                'display_name': '提取文本',
                'category': '变量提取',
                'description': '提取元素文本到变量',
                'color': 'geekblue',
                'requires_element': True,
                'requires_value': True,
                'value_format': '变量名',
                'value_example': 'username',
                'value_description': '将元素文本存储到指定变量，使用${变量名}引用',
            },
            'extract_attribute': {
                'display_name': '提取属性',
                'category': '变量提取',
                'description': '提取元素属性到变量',
                'color': 'geekblue',
                'requires_element': True,
                'requires_value': True,
                'value_format': '属性名:变量名',
                'value_example': 'text:username',
                'value_description': '属性名和变量名，如text:val将text属性存入val变量',
            },
            'set_variable': {
                'display_name': '设置变量',
                'category': '变量提取',
                'description': '设置变量值',
                'color': 'geekblue',
                'requires_element': False,
                'requires_value': True,
                'value_format': '变量名=值',
                'value_example': 'counter=0',
                'value_description': '设置变量值，支持变量引用如count=${count}+1',
            },
            'get_variable': {
                'display_name': '获取变量',
                'category': '变量提取',
                'description': '获取变量值',
                'color': 'geekblue',
                'requires_element': False,
                'requires_value': True,
                'value_format': '变量名',
                'value_example': 'username',
                'value_description': '获取并打印变量值，用于调试',
            },

            # ========== ADB设备操作 ==========
            'adb_install': {
                'display_name': '安装应用',
                'category': 'ADB操作',
                'description': '安装APK文件到设备',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'APK文件路径',
                'value_example': '/sdcard/app.apk',
                'value_description': '设备上的APK文件路径或本地路径',
            },
            'adb_uninstall': {
                'display_name': '卸载应用',
                'category': 'ADB操作',
                'description': '卸载应用包',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '包名',
                'value_example': 'com.example.app',
                'value_description': '应用的包名',
            },
            'adb_start_app': {
                'display_name': '启动应用',
                'category': 'ADB操作',
                'description': '通过ADB启动应用',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '包名或package+activity',
                'value_example': 'com.example.app',
                'value_description': '应用包名，或使用package/activity格式',
            },
            'adb_stop_app': {
                'display_name': '停止应用',
                'category': 'ADB操作',
                'description': '通过ADB停止应用',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '包名',
                'value_example': 'com.example.app',
                'value_description': '要停止的应用包名',
            },
            'adb_restart_app': {
                'display_name': '重启应用',
                'category': 'ADB操作',
                'description': '通过ADB重启应用',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '包名',
                'value_example': 'com.example.app',
                'value_description': '要重启的应用包名',
            },
            'adb_clear_app': {
                'display_name': '清除应用数据',
                'category': 'ADB操作',
                'description': '清除应用数据',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '包名',
                'value_example': 'com.example.app',
                'value_description': '要清除数据的应用包名',
            },
            'adb_tap': {
                'display_name': '点击坐标',
                'category': 'ADB操作',
                'description': '点击屏幕坐标',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'x,y',
                'value_example': '500,1000',
                'value_description': '屏幕坐标x,y（像素）',
            },
            'adb_swipe': {
                'display_name': 'ADB滑动',
                'category': 'ADB操作',
                'description': '通过ADB滑动',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'x1,y1,x2,y2,duration',
                'value_example': '500,1000,500,500,300',
                'value_description': '起点x1,y1到终点x2,y2，持续时间（毫秒）',
            },
            'adb_key_event': {
                'display_name': '按键事件',
                'category': 'ADB操作',
                'description': '发送按键事件',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '键码或键名',
                'value_example': 'KEYCODE_HOME 或 3',
                'value_description': 'Android键码（如KEYCODE_HOME）或数字键码',
            },
            'adb_input_text': {
                'display_name': 'ADB输入文本',
                'category': 'ADB操作',
                'description': '通过ADB输入文本',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '文本内容',
                'value_example': 'hello world',
                'value_description': '要输入的文本（不支持中文）',
            },
            'adb_shell': {
                'display_name': '执行Shell',
                'category': 'ADB操作',
                'description': '执行ADB shell命令',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'shell命令',
                'value_example': 'pm list packages',
                'value_description': '要执行的shell命令',
            },
            'adb_push_file': {
                'display_name': '推送文件',
                'category': 'ADB操作',
                'description': '推送文件到设备',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '本地路径,设备路径',
                'value_example': 'C:/file.txt,/sdcard/file.txt',
                'value_description': '本地文件路径和目标设备路径',
            },
            'adb_pull_file': {
                'display_name': '拉取文件',
                'category': 'ADB操作',
                'description': '从设备拉取文件',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': '设备路径,本地路径',
                'value_example': '/sdcard/file.txt,C:/file.txt',
                'value_description': '设备文件路径和本地保存路径',
            },

            # ========== Appium操作 ==========
            'get_text': {
                'display_name': '获取文本',
                'category': 'Appium操作',
                'description': '获取元素文本内容',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '获取元素的text属性值',
            },
            'get_attribute': {
                'display_name': '获取属性',
                'category': 'Appium操作',
                'description': '获取元素属性值',
                'color': 'purple',
                'requires_element': True,
                'requires_value': True,
                'value_format': '属性名',
                'value_example': 'content-desc',
                'value_description': '要获取的属性名（如text、content-desc、resource-id等）',
            },
            'get_location': {
                'display_name': '获取位置',
                'category': 'Appium操作',
                'description': '获取元素位置',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '获取元素在屏幕上的坐标位置',
            },
            'get_size': {
                'display_name': '获取大小',
                'category': 'Appium操作',
                'description': '获取元素大小',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '获取元素的宽度和高度',
            },
            'is_displayed': {
                'display_name': '是否显示',
                'category': 'Appium操作',
                'description': '检查元素是否显示',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '返回元素是否在屏幕上可见',
            },
            'is_enabled': {
                'display_name': '是否可用',
                'category': 'Appium操作',
                'description': '检查元素是否可用',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '返回元素是否处于可用状态',
            },
            'is_selected': {
                'display_name': '是否选中',
                'category': 'Appium操作',
                'description': '检查元素是否选中',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '返回元素是否被选中',
            },
            'scroll_to': {
                'display_name': '滚动到元素',
                'category': 'Appium操作',
                'description': '滚动到指定元素',
                'color': 'purple',
                'requires_element': True,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '自动滚动屏幕直到目标元素可见',
            },

            # ========== 系统操作 ==========
            'start_activity': {
                'display_name': '启动Activity',
                'category': '系统操作',
                'description': '启动指定Activity',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'package/activity',
                'value_example': 'com.example.app/.MainActivity',
                'value_description': '完整的Activity名称，包含包名',
            },
            'screenshot': {
                'display_name': '截图',
                'category': '系统操作',
                'description': '截取设备屏幕',
                'color': 'gold',
                'requires_element': False,
                'requires_value': False,
                'value_format': '文件名（可选）',
                'value_example': 'screenshot_01.png',
                'value_description': '可选参数，截图保存的文件名',
            },
            'get_current_activity': {
                'display_name': '获取当前Activity',
                'category': '系统操作',
                'description': '获取当前Activity',
                'color': 'gold',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '获取当前显示的Activity信息',
            },
            'open_notifications': {
                'display_name': '打开通知栏',
                'category': '系统操作',
                'description': '打开系统通知栏',
                'color': 'gold',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '下拉打开系统通知栏',
            },
            'toggle_location': {
                'display_name': '切换定位',
                'category': '系统操作',
                'description': '开关定位服务',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'on/off',
                'value_example': 'on',
                'value_description': 'on开启定位，off关闭定位',
            },
            'toggle_wifi': {
                'display_name': '切换WiFi',
                'category': '系统操作',
                'description': '开关WiFi',
                'color': 'gold',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'on/off',
                'value_example': 'on',
                'value_description': 'on开启WiFi，off关闭WiFi',
            },

            # ========== 高级操作 ==========
            'toast_check': {
                'display_name': '检查Toast',
                'category': '高级操作',
                'description': '检查Toast提示',
                'color': 'magenta',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'Toast文本',
                'value_example': '操作成功',
                'value_description': '检查是否出现指定文本的Toast提示',
            },
            'webview_switch': {
                'display_name': '切换WebView',
                'category': '高级操作',
                'description': '切换到WebView上下文',
                'color': 'magenta',
                'requires_element': False,
                'requires_value': True,
                'value_format': 'WebView名称',
                'value_example': 'WEBVIEW_com.example.app',
                'value_description': '要切换到的WebView上下文名称',
            },
            'native_app_switch': {
                'display_name': '切换原生应用',
                'category': '高级操作',
                'description': '切换到原生应用上下文',
                'color': 'magenta',
                'requires_element': False,
                'requires_value': False,
                'value_format': '无需参数',
                'value_example': '',
                'value_description': '从WebView切换回原生应用上下文',
            },
        }

        # 检查StepExecutor中实际支持的操作
        executor_instance = StepExecutor(driver=None, task=None)
        supported_actions = set()

        # 获取所有_execute_xxx方法
        for attr_name in dir(executor_instance):
            if attr_name.startswith('_execute_'):
                action_type = attr_name.replace('_execute_', '')
                supported_actions.add(action_type)

        # 构建能力列表
        for action_type, definition in builtin_actions.items():
            if action_type in supported_actions:
                # 提取config_schema字段（不包含在主字段中）
                config_schema = {
                    'value_format': definition.get('value_format', ''),
                    'value_example': definition.get('value_example', ''),
                    'value_description': definition.get('value_description', ''),
                }

                # 移除config_schema专用字段
                main_definition = {k: v for k, v in definition.items()
                                   if k not in ['value_format', 'value_example', 'value_description']}

                capabilities.append({
                    'type_code': action_type,
                    'first_seen_executor_id': self.executor_id,
                    'implementation_version': '1.0',
                    'config_schema': config_schema,
                    **main_definition
                })

        # TODO: 扫描插件目录
        # capabilities.extend(self._scan_plugin_actions())

        return capabilities

    def _get_hostname(self) -> str:
        """获取主机名"""
        import socket
        return socket.gethostname()

    def _get_ip_address(self) -> Optional[str]:
        """获取IP地址"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None


# 全局实例
_registration_service: Optional[CapabilityRegistrationService] = None


def get_registration_service() -> Optional[CapabilityRegistrationService]:
    """获取注册服务实例"""
    return _registration_service


def init_registration_service(backend_url: str, executor_id: str, executor_version: str):
    """初始化注册服务"""
    global _registration_service
    _registration_service = CapabilityRegistrationService(
        backend_url=backend_url,
        executor_id=executor_id,
        executor_version=executor_version
    )
    return _registration_service
