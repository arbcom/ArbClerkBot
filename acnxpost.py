import mwclient
import json
import wikitextparser as parser
import logging
import re

__lastrev = 0

def run(wiki):
    global __lastrev
    
    ACN = u"Wikipedia:Arbitration Committee/Noticeboard"
    TACN = u"Wikipedia talk:Arbitration Committee/Noticeboard"
    AN = u"Wikipedia:Administrators' noticeboard"
    AUTH = u"User:ArbClerkBot/Authorized users"

    """
    load WP:ACN
    for each section
    if section
        is level 2
        ends with a signature
        does not contain a link to WT:ACN
    then
        ensure that the last editor of the page is an arb or clerk (userlink on AUTH)
        add Discuss this link
        create section on WT:ACN, if one by the same name does not already exist
        xpost to AN, if a section by the same name does not already exist
        search for links to user pages, ensure they are within the current section, and xpost

    Any error (edit conflict, protected page, etc.) should result in the bot trying the edit again on the next run.
    To prevent duplicates, it errs on the side of not creating sections with duplicate names.
    """

    try:
        authusers = []
        def auth():
            lasteditor = wiki.revisions([page.revision])[0]['user']
            authpage = wiki.pages[AUTH]
            authusers.extend([user.page_title for user in authpage.links(namespace=2)])
            return lasteditor in authusers

        def xpost(target, title, announcement, ignoreerrors=False):
            try:
                logging.info('Crossposting to ' + target + '#' + title)
                p = wiki.pages[target]
                if p.text().find("== " + title + " ==") == -1:
                    p.save(p.text() + '\n== ' + title + ' ==\n' + announcement, '/* ' + title + ' */ Crossposting from [[' + ACN + ']] (bot)', minor=False, bot=False)
                else:
                    logging.warning('Section already exists.')
            except Exception as e:
                if ignoreerrors:
                    logging.error("Exception occurred", exc_info=True)
                else:
                    raise e
                        
        page = wiki.pages[ACN]
        if page.revision != __lastrev:
            __lastrev = page.revision
            logging.info('Current revision: ' + str(__lastrev))
            parsed = parser.parse(page.text())
            updated = False
            for section in parsed.sections:
                if section.level == 2 and section.contents.strip().endswith("(UTC)") and section.contents.find(TACN) == -1:
                    if auth():
                        title = section.title.strip()
                        logging.info('Found new section ' + ACN + '#' + title)
                        a = "\n: Discuss this at: '''[[" + TACN + "#" + title + "]]'''{{subst:hes}}\n\n"
                        announcement = section.contents.strip() + a
                        section.contents = announcement

                        logging.info('Creating talk section ' + TACN + '#' + title)
                        talkpage = wiki.pages[TACN]
                        a = "\n== " + title + " ==\n: [[" + ACN + "#" + title + "|'''Original announcement''']]{{subst:hes}}\n"
                        if talkpage.text().find("== " + title + " ==") == -1:
                            talkpage.save(talkpage.text() + a, '/* ' + title + ' */ Creating talk page section (bot)', minor=True, bot=True)
                        else:
                            logging.warning('Section already exists.')

                        xpost(AN, title, announcement)

                        xpostusers = []
                        for ul in [user.page_title for user in page.links(namespace=2)]:
                            if re.search('[:|]' + ul + '[]|}]', announcement) and ul not in authusers:
                                xpostusers.append("User talk:" + ul)
                        for user in xpostusers:
                            xpost(user, title, announcement, True)

                        updated = True
                    else:
                        break

            if updated and parsed != page.text():
                t = str(parsed)
                while t.find('\n\n\n') > -1:
                    t = t.replace('\n\n\n', '\n\n')
                logging.info('Updating ' + ACN)
                page.save(t, summary='Adding links to talk page sections (bot)', minor=True, bot=True)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
