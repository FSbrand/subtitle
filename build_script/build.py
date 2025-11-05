#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕程序构建脚本
优化版本 - 减小exe体积，修复缺失模块问题
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理旧的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✓ 已清理: {dir_name}/")
            except PermissionError:
                print(f"⚠️ 无法删除 {dir_name}/ (文件可能正在使用)")
                # 尝试删除目录中的单个文件
                try:
                    for root, dirs, files in os.walk(dir_name):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                            except:
                                pass
                    print(f"✓ 已部分清理: {dir_name}/")
                except:
                    print(f"❌ 跳过清理: {dir_name}/")
            except Exception as e:
                print(f"❌ 清理失败 {dir_name}/: {e}")

def build_executable():
    """构建可执行文件"""
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    main_py_path = project_root / "main.py"
    
    if not main_py_path.exists():
        print(f"❌ 错误: 找不到 {main_py_path}")
        return False
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # PyInstaller命令 - 添加更多必要的隐藏导入
    cmd = [
        'pyinstaller',
        '--onefile',
        '--noconsole',
        '--name=subtitle_optimized',
        '--distpath=build/dist',
        '--workpath=build/temp',
        '--specpath=build',
        # 核心Python模块
        '--hidden-import=urllib',
        '--hidden-import=urllib.request',
        '--hidden-import=urllib.parse',
        '--hidden-import=urllib.error',
        '--hidden-import=http',
        '--hidden-import=http.client',
        '--hidden-import=pathlib',
        '--hidden-import=importlib',
        '--hidden-import=importlib.metadata',
        '--hidden-import=importlib.util',
        # 邮件相关模块
        '--hidden-import=email',
        '--hidden-import=email.mime',
        '--hidden-import=email.mime.text', 
        '--hidden-import=email.utils',
        # WebSocket相关
        '--hidden-import=websockets',
        '--hidden-import=websockets.server',
        '--hidden-import=websockets.legacy',
        '--hidden-import=websockets.legacy.server',
        '--hidden-import=websockets.legacy.client',
        # PyQt5相关
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtGui',
        # 其他必需模块
        '--hidden-import=asyncio',
        '--hidden-import=json',
        '--hidden-import=base64',
        '--hidden-import=hashlib',
        '--hidden-import=hmac',
        '--hidden-import=time',
        '--hidden-import=threading',
        '--hidden-import=logging',
        '--hidden-import=logging.handlers',
        '--hidden-import=configparser',
        '--hidden-import=requests',
        '--hidden-import=ssl',
        # 排除不需要的模块以减小体积
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=sqlite3',
        '--exclude-module=unittest',
        '--exclude-module=pydoc',
        '--exclude-module=multiprocessing',
        '--exclude-module=xml',
        '--exclude-module=test',
        '--exclude-module=distutils',
        '--exclude-module=setuptools',
        str(main_py_path)
    ]
    
    print("📦 开始构建可执行文件...")
    print(f"🎯 主文件: {main_py_path}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            exe_path = project_root / "build" / "dist" / "subtitle_optimized.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / 1024 / 1024
                print(f"✅ 构建成功!")
                print(f"📄 输出文件: {exe_path}")
                print(f"📊 文件大小: {size_mb:.1f} MB")
                
                # 自动复制translations.txt到dist目录
                try:
                    translations_src = project_root / "translations.txt"
                    translations_dst = project_root / "build" / "dist" / "translations.txt"
                    
                    if translations_src.exists():
                        shutil.copy2(translations_src, translations_dst)
                        print(f"📝 已复制翻译词典: {translations_dst}")
                    else:
                        print("⚠️  未找到translations.txt文件，将使用API翻译")
                        
                    # 复制图标文件
                    icon_src = project_root / "icon_simple.svg"
                    icon_dst = project_root / "build" / "dist" / "icon_simple.svg"
                    
                    if icon_src.exists():
                        shutil.copy2(icon_src, icon_dst)
                        print(f"🎨 已复制图标文件: {icon_dst}")
                        
                except Exception as e:
                    print(f"⚠️  复制配置文件时出错: {e}")
                    
                return True
            else:
                print("❌ 构建失败: 找不到输出文件")
                return False
        else:
            print("❌ 构建失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 字幕程序构建器")
    print("=" * 50)
    
    # 检查依赖
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("❌ 请先安装 PyInstaller: pip install pyinstaller")
        return
    
    # 清理旧文件
    clean_build_dirs()
    
    # 构建
    if build_executable():
        print("\n🎉 构建完成!")
        print("📍 可执行文件位置: build/dist/subtitle_optimized.exe")
    else:
        print("\n💥 构建失败!")

if __name__ == "__main__":
    main() 
