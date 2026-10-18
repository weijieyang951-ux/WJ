import os, sys
import requests
def main():
    token=os.getenv('TELEGRAM_BOT_TOKEN'); chat=os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat: print('Telegram not configured'); return
    try:
        r=requests.post('https://api.telegram.org/bot'+token+'/sendMessage',json={'chat_id':chat,'text':'US equity research: '+sys.argv[1]},timeout=20)
        if r.status_code!=200: raise RuntimeError('Telegram delivery failed')
    except requests.RequestException: raise RuntimeError('Telegram transport failed; token redacted') from None
if __name__=='__main__': main()
