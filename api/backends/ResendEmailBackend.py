from typing import Any, Dict, List, Union

import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives


class ResendEmailBackend(BaseEmailBackend):
    """Resend email backend, from django email service"""

    def __init__(self, fail_silently=..., **kwargs):
        super().__init__(fail_silently, **kwargs)
        self.api_key = getattr(settings, "RESEND_API_KEY", "")

    def send_messages(
        self, email_messages: List[Union[EmailMessage, EmailMultiAlternatives]]
    ) -> int:
        """method of send email, will return the number of email was send"""
        if not email_messages:
            return 0

        resend.api_key = self.api_key
        count = 0

        for message in email_messages:
            sent = self._send(message)
            if sent:
                count += 1

        return count

    def _send(self, email_message: Union[EmailMessage, EmailMultiAlternatives]) -> bool:
        """send a single email"""
        try:
            recipients = email_message.to

            params: resend.Emails.SendParams = {
                "from": email_message.from_email,
                "to": recipients,
                "subject": email_message.subject,
                # "html": email_message.body,
                "text": email_message.body,
            }

            if email_message.cc:
                params["cc"] = email_message.cc
            if email_message.bcc:
                params["bcc"] = email_message.bcc

            if email_message.attachments:
                attachments: List[Dict[str, Any]] = []
                for attachment in email_message.attachments:
                    if isinstance(attachments, tuple) and len(attachment) >= 2:
                        attach_data: Dict[str, Any] = {
                            "filename": attachment[0],
                            "content": attachment[1],
                        }
                        if len(attachment) > 2:
                            attach_data["content_type"] = attachment[2]
                        attachments.append[attachment]
                if attachments:
                    params["attachments"] = attachments

            response = resend.Emails.send(params)
            print(response["id"])
            return "id" in response
        except Exception as e:
            if not self.fail_silently:
                raise e
            return False


# doc: https://docs.djangoproject.com/zh-hans/5.1/topics/email/#defining-a-custom-email-backend
