import mwclient
import json
import wikitextparser as parser
import logging

def run(wiki):
    ACN = u"Wikipedia:Arbitration Committee/Noticeboard"
    TACN = u"Wikipedia talk:Arbitration Committee/Noticeboard"
    AN = u"Wikipedia:Administrators' noticeboard"
    AUTH = u"User:Arbitration Bot/Authorized users"

    """
    load WP:ACN
    ensure that the last editor is an arb or clerk (userlink on AUTH)
    for each section
    if section
        is level 2
        ends with a signature
        does not contain a link to WT:ACN
    then
        add Discuss this link
        create section on WT:ACN, if one by the same name does not already exist
        xpost to AN, if a section by the same name does not already exist

    Any error (edit conflict, protected page, etc.) should result in the bot trying the edit again on the next run.
    To prevent duplicates, it errs on the side of not creating sections with duplicate names.
    """

    try:
        page = wiki.pages[ACN]
        pagetext = page.text()
        lastuser = wiki.revisions([page.revision])[0]['user']
        authpage = wiki.pages[AUTH]
        authusers = [user.page_title for user in authpage.links(namespace=2)]
        if lastuser in authusers:
            parsed = parser.parse(pagetext)
            for section in parsed.sections:
                if section.level == 2 and section.contents.strip().endswith("(UTC)") and section.contents.find(TACN) == -1:
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

                    xpost = [AN]
                    xpost_content = "\n== " + title + " ==\n" + announcement
                    for target in xpost:
                        logging.info('Crossposting to ' + target + '#' + title)
                        p = wiki.pages[target]
                        if p.text().find("== " + title + " ==") == -1:
                            p.save(p.text() + xpost_content, '/* ' + title + ' */ Crossposting from [[WP:ACN]] (bot)', minor=False, bot=False)
                        else:
                            logging.warning('Section already exists.')

            if parsed != page.text():
                t = str(parsed)
                while t.find('\n\n\n') > -1:
                    t = t.replace('\n\n\n', '\n\n')
                logging.info('Updating ' + ACN)
                page.save(t, summary='Adding links to talk page (bot)', minor=True, bot=True)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
