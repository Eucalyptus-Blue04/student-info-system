from app import app, db
from db import User, UserRole


def init_admin():
    """初始化管理员账户"""
    with app.app_context():
        # 检查是否已存在管理员账户
        admin = User.query.filter_by(role=UserRole.ADMIN.value).first()
        if not admin:
            admin = User(
                username='admin',
                password='admin',  # 默认密码
                real_name='系统管理员',
                role=UserRole.ADMIN.value
            )
            db.session.add(admin)
            try:
                db.session.commit()
                app.logger.info('管理员账户创建成功')
                print('管理员账户创建成功！')
                print('用户名: admin')
                print('密码: admin')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'管理员账户创建失败: {str(e)}')
                print(f'管理员账户创建失败！错误：{str(e)}')
        else:
            print('管理员账户已存在！')


if __name__ == '__main__':
    init_admin()
