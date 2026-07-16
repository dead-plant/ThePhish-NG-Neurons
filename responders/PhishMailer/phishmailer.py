#!/usr/bin/env python3

from cortexutils.responder import Responder
from email_validator import validate_email, EmailNotValidError

class NoRecipientFoundError(Exception):
    pass

class PhishMailer(Responder):
    def __init__(self):
        super().__init__(self)
        self.from_addr = self.get_param('config.from_addr', None, "Missing from address")
        self.smtp_host = self.get_param('config.smtp_host', None, "Missing SMTP host")
        self.smtp_port = int(self.get_param('config.smtp_port', None, "Missing SMTP port"))
        self.smtp_encryption = self.get_param('config.smtp_encryption', None, "Missing encryption mode")
        self.smtp_verify = bool(self.get_param('config.smtp_verify', None, "Missing tls verify"))
        self.smtp_user = self.get_param('config.smtp_user', None,None)
        self.smtp_password = self.get_param('config.smtp_password', None, None)

        self.description_lines = self.get_param('data.description', None, "Can't get description").splitlines()

    def run(self):
        Responder.run(self)

        try:
            recipient, start_index = self.extract_recipient()


        except NoRecipientFoundError:
            self.error('No recipient found in description.')
        except EmailNotValidError:
            self.error("Recipient email found but invalid.")
        except Exception as exc:
            self.error(str(exc))

    def extract_recipient(self):
        for index, line in enumerate(self.description_lines):
            if line.startswith("#PhishMailer: mailto: "):
                data = line.replace("#PhishMailer: mailto: ", "").strip()

                return validate_email(data, check_deliverability=True), index+1

        raise NoRecipientFoundError("No recipient found in description.")


if __name__ == '__main__':
    PhishMailer().run()
