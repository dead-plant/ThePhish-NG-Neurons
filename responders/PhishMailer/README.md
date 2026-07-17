# PhishMailer

A Cortex responder that sends emails using SMTP.

## Table of Contents

- [Description](#description)
- [How to use](#how-to-use)
- [Config options](#config-options)

## Description

PhishMailer sends part of a TheHive case or case_task description as an email. A `#PhishMailer` directive in the description defines one or more recipients and, optionally, the email subject. Every line after the directive becomes the email body.

The responder supports unencrypted SMTP, STARTTLS and implicit TLS. After an email is sent successfully, it reports the recipients, subject and message ID, and adds the `PhishMailer:mail-sent` tag to the case.

## How to use

1. [Install the responder](../../docs/install.md) and configure its SMTP connection in Cortex.
2. Add a directive to the description of a TheHive case or case_task, it has to be at the beginning of a line:

   ```text
   #PhishMailer; subject: "Suspected phishing email"; mailto:analyst@example.com; mailto:security@example.com;

   A suspicious email was reported. Please review the case details and attached observables.
   ```

3. Run the PhishMailer responder on the case or case_task. In this example, everything after the directive will be sent to both recipients.

The directive uses fields separated by semicolons and must end with a semicolon. It accepts one optional quoted `subject` field and one or more `mailto` fields. Whitespace around separators is allowed, and a quoted subject may contain semicolons. Unknown fields, invalid recipient addresses and duplicate subject fields cause the responder to stop with an error. Duplicate recipients are removed automatically.

If `subject` is omitted, PhishMailer creates one in the following format:

```text
TheHive Case [case-id]: case title
```

For a case_task, `Case` is replaced with `Task`. Custom subjects are limited to 120 characters, and the title portion of a generated subject is limited to 60 characters.

## Config options

| Name              | Required | Default | Description                                                                                                |
|-------------------|----------|---------|------------------------------------------------------------------------------------------------------------|
| `from_addr`       | Yes      | -       | Valid sender email address used in the `From` header.                                                      |
| `smtp_host`       | Yes      | -       | Hostname or IP address of the SMTP server.                                                                 |
| `smtp_port`       | Yes      | `465`   | Port used to connect to the SMTP server.                                                                   |
| `smtp_encryption` | Yes      | `tls`   | Connection mode: `tls` for implicit TLS, `starttls` for starttls, or `none` for an unencrypted connection. |
| `smtp_verify`     | Yes      | `true`  | Whether to verify the SMTP server's TLS certificate.                                                       |
| `smtp_user`       | No       | -       | SMTP authentication username. Must be provided together with `smtp_password`.                              |
| `smtp_password`   | No       | -       | SMTP authentication password. Must be provided together with `smtp_user`.                                  |

SMTP authentication is refused when `smtp_encryption` is set to `none`.

