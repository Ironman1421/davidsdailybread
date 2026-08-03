# External reader-intake and newsletter cutover checklist

Status: prepared only, execution is not authorized

Owner and approval authority: David Friedhof

This checklist is intentionally separate from the repository cutover. Stop
before every unchecked action below until David gives explicit approval for the
named external system. Do not submit test reader data, export lists, delete
rows, change billing, or copy private values into screenshots, tickets, or logs.

For each approved action, record the operator, UTC timestamp, setting before,
setting after, and a sanitized verification result. Never record subscriber
addresses, reader text, bylines, form identifiers, sheet identifiers, or tokens.

## Buttondown

- [ ] Record David's explicit approval for Buttondown account mutation.
- [ ] Open the newsletter's Subscribing settings.
- [ ] Enable **Private mode**, acknowledge the warning, and save. Buttondown
      documents that Private mode blocks public subscriptions, including form
      endpoint submissions.
- [ ] Confirm no draft, scheduled issue, welcome automation, sending credential,
      paid add-on, import, or list reactivation is active. Do not create or test
      any of these items.
- [ ] Preserve existing subscriber records and privacy/deletion handling. Do not
      add, unsubscribe, reactivate, export, or delete a subscriber in this step.
- [ ] In a signed-out session, verify the hosted signup page and a legacy form
      endpoint cannot enroll a new address. Do not make a test submission.
- [ ] Leave historical newsletter archives unchanged unless David separately
      approves an archive-visibility change.

Reference: https://docs.buttondown.com/private-mode

## Google Form

- [ ] Record David's explicit approval for Google Form mutation.
- [ ] Open the published form, select **Published**, turn **Accepting responses**
      off, set a neutral closure message that reader submissions are temporarily
      paused, and save.
- [ ] In **Responses**, use **More** then **Unlink form** to stop future Sheet
      writes while preserving existing responses. Do not delete a response or
      the form.
- [ ] Review responder access without adding collaborators or publishing a new
      link.
- [ ] In a signed-out session, verify the legacy responder URL shows the closure
      message and has no submit path. Do not enter reader data.

References: https://support.google.com/docs/answer/139706 and
https://support.google.com/docs/answer/2917686

## Google Sheet

- [ ] Record David's explicit approval for Google Sheet mutation.
- [ ] Open **File**, **Share**, **Publish to web**, expand **Published content and
      settings**, and select **Stop publishing**.
- [ ] Set Drive general access to **Restricted**. Review form and Sheet
      collaborators separately because Google does not synchronize their access
      changes.
- [ ] Preserve every existing row. Do not download, export, copy, move, edit, or
      delete reader data during this cutover.
- [ ] In a signed-out session, verify the former published HTML and CSV URLs no
      longer expose data. Check only status and access behavior; do not print or
      log response bodies.

References: https://support.google.com/docs/answer/183965 and
https://support.google.com/drive/answer/2494893

## GitHub Issues

Repository scan result: no issue form, issue template, new-issue URL, or public
reader-intake reference was found in the current default-branch source.

- [ ] Record David's explicit approval for GitHub repository-settings mutation.
- [ ] Inspect repository **Settings**, **General**, **Features** and confirm
      whether Issues is enabled. Do not create an issue during verification.
- [ ] If Issues has been used as reader intake, disable it or restrict it to
      collaborators. Preserve ordinary engineering issues and all history unless
      David explicitly approves a broader shutdown.
- [ ] Privately audit existing issue bodies and comments for reader data without
      copying their contents into logs.
- [ ] In a signed-out session, verify there is no public reader-submission issue
      template or new-issue route.

Reference: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/disabling-issues

## Completion gate

- [ ] All four systems have separate explicit approval receipts.
- [ ] All sanitized verification evidence is recorded without private data.
- [ ] Repository deployment is separately approved and completed.
- [ ] A post-deployment public scan reports zero active submission endpoints,
      zero private email addresses, and no public reader-row artifact.
- [ ] David records whether the pause remains in force or a verified private
      intake boundary may proceed.
