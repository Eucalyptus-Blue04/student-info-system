from app import app, db
from init_admin import init_admin

def reset_db():
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        # 初始化管理员账户
        init_admin()

if __name__ == '__main__':
    print("正在重置数据库...")
    reset_db()
    print("数据库重置完成！")
