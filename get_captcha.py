from io import BytesIO
from random import choices
from captcha.image import ImageCaptcha
from flask import make_response
from PIL import Image

def gen_captcha(content="abcdefghijklmnopqrstuvwxyz1234567890"):
    #生成验证码
    image = ImageCaptcha()
    # 获取字符串
    captcha_text = "".join(choices(content, k=4))
    # 生成图像
    captcha_image = Image.open(image.generate(captcha_text))
    return captcha_text, captcha_image

# 生成验证码
def get_captcha_code_and_content():
    code, image = gen_captcha()
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return code, buffer

if __name__ == '__main__':
    code, content = get_captcha_code_and_content()
    print(code, content)