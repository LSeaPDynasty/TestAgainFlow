"""
初始化超级管理员账户
用于首次部署时创建默认的超级管理员用户
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.user_service import _hash_password


def create_superuser(username: str, email: str, password: str):
    """创建超级管理员用户"""
    db = SessionLocal()

    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"错误: 用户 '{username}' 已存在")
            return False

        # 创建超级管理员
        admin_user = User(
            username=username,
            email=email,
            password_hash=_hash_password(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )

        db.add(admin_user)
        db.commit()

        print(f"成功创建超级管理员用户:")
        print(f"  用户名: {username}")
        print(f"  邮箱: {email}")
        print(f"  角色: 超级管理员")
        print(f"\n请妥善保管登录凭据！")
        return True

    except Exception as e:
        db.rollback()
        print(f"创建用户失败: {e}")
        return False
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("TestFlow 超级管理员初始化工具")
    print("=" * 60)
    print()

    # 获取用户输入
    username = input("请输入超级管理员用户名 [默认: admin]: ").strip() or "admin"
    email = input("请输入邮箱 [可选]: ").strip() or None
    password = input("请输入密码: ").strip()

    if not password:
        print("错误: 密码不能为空")
        return

    # 确认密码
    confirm_password = input("请确认密码: ").strip()
    if password != confirm_password:
        print("错误: 两次输入的密码不一致")
        return

    print()
    # 创建用户
    if create_superuser(username, email, password):
        print("\n超级管理员账户创建完成！")
        print("您现在可以使用该账户登录TestFlow系统。")
    else:
        print("\n超级管理员账户创建失败，请检查错误信息。")


if __name__ == "__main__":
    main()
