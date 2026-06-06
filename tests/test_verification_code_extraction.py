import json
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EMAILS_JS_PATH = ROOT_DIR / 'static' / 'js' / 'index' / '05-emails.js'


def _extract_verification_code_helpers(source):
    start = source.index('const VERIFICATION_CODE_CONTEXT_PATTERNS')
    end = source.index('function getNormalMailboxRemoteMethod', start)
    return source[start:end]


def _find_verification_codes(*emails):
    source = EMAILS_JS_PATH.read_text(encoding='utf-8')
    helper_source = _extract_verification_code_helpers(source)
    script = f"""
{helper_source}
const emails = {json.dumps(list(emails), ensure_ascii=False)};
console.log(JSON.stringify(emails.map(email => findVerificationCode(email))));
"""
    result = subprocess.run(
        ['node', '-e', script],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_extracts_chinese_login_verification_code_from_preview():
    [code] = _find_verification_codes({
        'subject': '你的临时 ChatGPT 登录代码',
        'body_preview': '输入此临时验证码以继续：\n\n492822\n\n如果你无意登录 ChatGPT，请重置密码。'
    })

    assert code == '492822'


def test_extracts_microsoft_security_code_from_labeled_line():
    [code] = _find_verification_codes({
        'subject': 'Personal Microsoft account security code',
        'body_preview': 'Security code: 925275\nOnly enter this code on an official website or app.'
    })

    assert code == '925275'


def test_extracts_alphanumeric_access_code():
    [code] = _find_verification_codes({
        'subject': 'Your temporary access code',
        'body_preview': 'Your access code is QZ524822.'
    })

    assert code == 'QZ524822'


def test_extracts_multilingual_verification_codes():
    codes = _find_verification_codes(
        {
            'subject': '您的登入驗證碼',
            'body_preview': '您的驗證碼是 135790，請勿分享。'
        },
        {
            'subject': '一時検証コード',
            'body_preview': 'この一時検証コードを入力して続行してください:\n\n822779\n\n検証コードをリクエストしていない場合、このメールは無視してください。'
        },
        {
            'subject': '인증 코드 안내',
            'body_preview': '계속하려면 인증 코드를 입력하세요.\n\n384920'
        },
        {
            'subject': 'Codice di verifica',
            'body_preview': 'Il tuo codice di verifica è 583921.'
        },
        {
            'subject': 'Code de vérification',
            'body_preview': 'Votre code de vérification est 492013.'
        },
        {
            'subject': 'رمز التحقق',
            'body_preview': 'رمز التحقق الخاص بك هو ٨٢٢٧٧٩'
        },
        {
            'subject': 'Código de verificación',
            'body_preview': 'Tu código de verificación es 219048.'
        },
        {
            'subject': 'Código de verificação',
            'body_preview': 'Seu código de verificação é 310246.'
        },
        {
            'subject': 'Код подтверждения',
            'body_preview': 'Ваш код подтверждения: 741852'
        },
    )

    assert codes == [
        '135790',
        '822779',
        '384920',
        '583921',
        '492013',
        '822779',
        '219048',
        '310246',
        '741852',
    ]


def test_ignores_dates_account_numbers_and_numbers_without_code_context():
    codes = _find_verification_codes(
        {
            'subject': 'Microsoft account security info was added',
            'body_preview': 'The following security info was added in 2026 for user vpnyong2026@163.com.'
        },
        {
            'subject': 'Daily report',
            'body_preview': 'Report created on 2026-06-06 at 09:20. Ticket 31581 is still open.'
        },
        {
            'subject': 'Plain notification',
            'body_preview': 'Your reference number is 492822.'
        },
    )

    assert codes == ['', '', '']
