import smtplib
import secrets
import string
import re


def generate_temp_password_and_check():
    alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$',
                    password):
        # print("Generated Password is not satisfying")
        return generate_temp_password_and_check()
    print(password)
    # print("Generated Password is satisfying")
    return password


def send_mail_to_reset_password(to, body):

    gmail_user = 'techblog.xcubelabs@gmail.com'
    gmail_password = 'techblog@123'

    password = generate_temp_password_and_check()

    sent_from = gmail_user
    subject = 'Temp Password'
    body = "Hello " + f'{body} ' + 'your temporary password is ' + f'{password}'

    email_text = f'Subject: {subject}' \
                 f'\n' \
                 f'\n' \
                 f'{body}'

    try:
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_password)
        smtp_server.sendmail(sent_from, to, email_text)
        smtp_server.close()
        # print("Email sent successfully!")
        return password
    except Exception as ex:
        print("Something went wrong….", ex)
        return "Error"
