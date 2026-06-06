import json
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EMAILS_JS_PATH = ROOT_DIR / 'static' / 'js' / 'index' / '05-emails.js'


def _extract_verification_code_helpers(source):
    start = source.index('const VERIFICATION_CODE_CONTEXT_PATTERN')
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
