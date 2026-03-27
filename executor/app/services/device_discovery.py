"""
设备自动发现和注册模块
执行引擎启动时自动发现连接的设备并注册到后端
"""
import subprocess
import logging
import asyncio
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DeviceAutoDiscovery:
    """设备自动发现和注册"""

    def __init__(self, ws_client):
        self.ws_client = ws_client
        self.known_devices = set()
        self.scan_interval = 30  # 每30秒扫描一次设备

    async def scan_and_register_devices(self):
        """扫描并注册设备"""
        try:
            devices = await self._get_connected_devices()
            logger.info(f"📱 扫描到 {len(devices)} 个设备")

            # 发送设备列表到后端
            await self.ws_client.send_device_update(devices)

            # 记录已发现的设备
            for device in devices:
                self.known_devices.add(device['serial'])

        except Exception as e:
            logger.error(f"❌ 扫描设备失败: {e}")

    async def _get_connected_devices(self) -> List[Dict[str, Any]]:
        """获取连接的设备列表"""
        try:
            # 使用adb devices命令获取设备
            process = await asyncio.create_subprocess_exec(
                'adb', 'devices',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"adb devices命令失败: {stderr}")
                return []

            # 解析设备列表
            devices = []
            lines = stdout.decode().strip().split('\n')

            for line in lines[1:]:  # 跳过第一行标题
                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    serial = parts[0].strip()
                    status = parts[1].strip()

                    # 只添加在线设备
                    if status in ['device', 'offline', 'unauthorized']:
                        # 获取设备详细信息
                        device_info = await self._get_device_info(serial)
                        devices.append({
                            'serial': serial,
                            'status': 'online' if status == 'device' else status,
                            **device_info
                        })

            return devices

        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []

    async def _get_device_info(self, serial: str) -> Dict[str, Any]:
        """获取设备详细信息"""
        device_info = {
            'model': 'Unknown',
            'os_version': 'Unknown',
            'manufacturer': 'Unknown'
        }

        try:
            # 获取设备型号
            process = await asyncio.create_subprocess_exec(
                'adb', '-s', serial, 'shell', 'getprop', 'ro.product.model',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()
            if process.returncode == 0:
                device_info['model'] = stdout.decode().strip()

            # 获取Android版本
            process = await asyncio.create_subprocess_exec(
                'adb', '-s', serial, 'shell', 'getprop', 'ro.build.version.release',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()
            if process.returncode == 0:
                device_info['os_version'] = 'Android ' + stdout.decode().strip()

            # 获取制造商
            process = await asyncio.create_subprocess_exec(
                'adb', '-s', serial, 'shell', 'getprop', 'ro.product.manufacturer',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()
            if process.returncode == 0:
                device_info['manufacturer'] = stdout.decode().strip()

        except Exception as e:
            logger.debug(f"获取设备 {serial} 详细信息失败: {e}")

        return device_info

    async def start_background_scan(self):
        """启动后台设备扫描"""
        logger.info("🔄 启动设备自动扫描...")

        # 立即扫描一次
        await self.scan_and_register_devices()

        # 后台定期扫描
        while True:
            try:
                await asyncio.sleep(self.scan_interval)
                await self.scan_and_register_devices()
            except asyncio.CancelledError:
                logger.info("⏹️ 设备扫描已停止")
                break
            except Exception as e:
                logger.error(f"❌ 设备扫描错误: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒重试