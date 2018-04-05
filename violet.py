#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import poplib, smtplib, email.utils, mailInit
from email.parser import Parser as ps
from email.message import Message as ms

#使用utf-8编码
codingFetch = mailInit.codingFetch
def toUnicode(msBytes, codingFetch=codingFetch):
    return [line.decode(codingFetch) for line in msBytes]

#分割地址列表
def splitAddrs(field):
    pairs = email.utils.getaddresses([field])
    return [email.utils.formataddr(pair) for pair in pairs]

#读取输入的文本信息
def inputMs():
    import sys
    From = input('From: ').strip()#strip: 去除首尾空格
    To = input('To: ').strip()
    To = splitAddrs(To)
    Subj = input('Subj: ').strip()
    
    print('Type message text, end with line="."')
    text = ''
    while True:
        line = sys.stdin.readline()
        if line == '.\n': break
        text += line
    return From, To, Subj, text

#发送邮件
def sendMs():
    From, To, Subj, text = inputMs()
    msg = ms()
    msg['From'] = From
    msg['To'] = ', '.join(To)
    msg['Subject'] = Subj
    msg['Date'] = email.utils.formatdate()
    msg.set_payload(text)
    
    server = smtplib.SMTP_SSL(mailInit.smtpServerName)
    server.ehlo(mailInit.smtpServerName)
    server.login(mailInit.sender, mailInit.mailPassWd)
    
    try:
        failed = server.sendmail(From, To, str(msg))
    except:
        print('Error - send failed')
    else:
        if failed: print('Failed:', failed)

#链接登录QQ邮箱的POP服务器，需要用SSL
def connectServer(serverName, user, passWd):
    print('Connecting...')
    
    server = poplib.POP3_SSL(serverName)
    server.user(user)
    server.pass_(passWd)#要用QQ给的授权码而不是密码
    
    print(server.getwelcome())
    
    return server

#载入邮箱里的邮件
def loadMs(serverName, user, passWd, loadFrom=1):
    
    server = connectServer(serverName, user, passWd)
    
    try:
        print(server.list())
        
        (msgCount, msgBytes) = server.stat()
        
        print('There are', msgCount,'mail message in', msgBytes, 'bytes')
        print('Retriveing...(Please keep waiting)')
        
        #开始抓取邮件
        msgList = []
        for i in range(loadFrom, msgCount+1):
            (hdr, message, octets) = server.retr(i)
            message = toUnicode(message)
            msgList.append('\n'.join(message))
    
    finally:
        server.quit()
    
    assert len(msgList) == (msgCount - loadFrom) + 1
    
    return msgList

#删除邮件
def deleteMs(serverName, user, passWd, toDelete, verify=True):
    print('To be deleted: ', toDelete)
    
    if verify and input('Delete?')[:1] not in ['y', 'Y']:
        print('Delete cancelled.')
    
    else:
        server = connectServer(serverName, user, passWd)
        try:
            print('Deleting messages from server...')
            for msgNum in toDelete:
                server.dele(msgNum)
        finally:
            server.quit()

#显示邮件目录
def showIndex(msgList):
    cnt = 0
    for msgText in msgList:
        msgHdrs = ps().parsestr(msgText, headersonly=True)
        
        cnt += 1
        print('%d:\t%d bytes' % (cnt, len(msgText)))
        
        for hdr in ('From', 'To', 'Data', 'Subject'):
            try:
                print('\t%-8s=>%s' % (hdr, msgHdrs[hdr]))
            except KeyError:
                print('\t%-8s=>(unknown)' % hdr)
        
        #每五个输入后暂停一下
        if cnt % 5 == 0:
            input('[Press Enter key]')

#对题头而非发送内容进行合并
def showMs(i, msgList):
    if 1 <= i <= len(msgList):
        #print(msgList[i-1])
        print('-' * 79)
        
        msg = ps().parsestr(msgList[i-1])
        content = msg.get_payload()
        
        if isinstance(content, str):
            content = content.rstrip() + '\n'
        
        print(content)
        print('-' * 79)
    else:
        print('Bad message number')

#把邮件保存到本地
def saveMs(i, mailFile, msgList):
    if 1 <= i <= len(msgList):
        saveFile = (open(mailFile, 'a', encoding=mailInit.codingFetch))
        saveFile.write('\n' + msgList[i-1] + '-' * 80 + '\n')
    else:
        print('Bad message number')

#返回命令的第二个参数
def msgNum(command):
    try:
        return int(command.split()[1])
    except:
        return -1

helpText = """
Avalilable commands:
i    - index display
l n? - list all message (or just message n)
d n? - mark all message for deletion (or just message n)
s n? - save all message to a file (or just message n)
m    - compose and send a new mail message
q    - quit Violet
?    - display this help text
"""

def interact(msgList, mailFile):
    showIndex(msgList)
    
    toDelete = []
    while True:
        try:
            command = input('[Violet] Action: (i, l, d, s, m, q, ?) ')
        except EOFError:
            command = 'q'
        
        if not command: command = '*'
        
        #退出
        if command =='q': break
        
        #索引
        elif command[0] == 'i': showIndex(msgList)
        
        #列表
        elif command[0] == 'l':
            if len(command) == 1:
                for i in range(1, len(msgList) + 1):
                    showMs(i, msgList)
            else:
                showMs(msgNum(command), msgList)
        
        #保存
        elif command[0] == 's':
            if len(command) == 1:
                for i in range(1, len(msgList) + 1):
                    saveMs(i, mailFile, msgList)
            else:
                saveMs(msgNum(command), mailFile, msgList)
        
        #删除
        elif command[0] == 'd':
            if len(command) == 1:
                toDelete = list(range(1, len(msgList) + 1))
            else:
                delNum = msgNum(command)
                if (1 <= delNum <= len(msgList)) and (delNum not in toDelete):
                    toDelete.append(delNum)
                else:
                    print('Bad message number')
        
        #邮件
        elif command == 'm':
            sendMs()
            #exectile('smtpmail.py', {})
        
        #帮助
        elif command[0] == '?':
            print(helpText)
        
        else:
            print('What? -- type "?" for commands help')
    
    return toDelete

if __name__ == '__main__':
    import mailInit#getpass
    mailServer = mailInit.popServerName
    mailUser = mailInit.popUserName
    mailFile = mailInit.saveMailFile
    mailPassWd = mailInit.mailPassWd#getpass.getpass('Password for %s: ' % mailServer)
    
    print('[Violet email client]')
    
    msgList = loadMs(mailServer, mailUser, mailPassWd)
    toDelete = interact(msgList, mailFile)
    if toDelete: deleteMs(mailServer, mailUser, mailPassWd, toDelete)
    
    print('Bye.')