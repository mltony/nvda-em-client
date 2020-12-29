# nvda-em-client
Accessibility improvements for eM Client

## Downloads
* Current development version: [eM Client add-on](https://github.com/mltony/nvda-em-client/releases/latest/download/EMClient.nvda-addon)

## About eM Client
eM Client is a multiplatform email client, that is free for personal use. It has many compelling features compared to Microsoft Outlook and Thunderbird, in particular it seems to be very fast. As of December 2020, please download this build of eM Client that has up-to-date accessibility improvements:

https://www.emclient.com/dist/v8.1.973/setup.msi

Free license needs to be requested here:

https://www.emclient.com/free-license

## Accessibility improvements
This add-on adds the following keystrokes:
* Control+arrows in message view to provide table-like navigation.
* NVDA+DownArrow in message view to read the last message in current thread.
* N and P to go to next or previous unread email in conversation view.
* NVDA+X in thread view to expand all messages in current thread.

Also this add-on adds following features:
* Conversation view is recognized as a table with table navigation commands working.
* Much less verbose announcement of conversations in conversations window.

## Other notes
* eM Client automatically combines emails into threads. Unlike Outlook and Thunderbird, you cannot see individual emails in the default configuration, and the basic unit appears to be thread, rather than email.
* In thread view eM Client presents individual messages as frames, and therefore the most convenient way to jump between messages is M and Shift+M keystrokes.
* In the main window press F6 and Shift+F6 to jump between folders tree view and conversations table.
