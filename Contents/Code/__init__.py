import re, os

def Start():
    pass
    
def ValidatePrefs():
    pass

class ChaptersAgent(Agent.Movies):

    name = 'Chapters Agent'
    languages = [Locale.Language.NoLanguage]
    primary_provider = False

    def convertTime(self, timeString):
        if (timeString == None):
            return None            
        m = re.match('(\d+):(\d+)(?::(\d+))?', timeString)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                time = int(groups[0]) * 60 + int(groups[1])
            else:
                time = int(groups[0]) * 60 * 60 + int(groups[1]) * 60 + int(groups[2])
            return time * 1000
        return None
                                                                          

    def search(self, results, media, lang):
        results.Append(MetadataSearchResult(id = media.id, name = media.name, year = None, score = 100, lang = lang))

    def update(self, metadata, media, lang):
        part = media.items[0].parts[0]
        path = os.path.dirname(part.file)
        (root_file, ext) = os.path.splitext(os.path.basename(part.file))

        Log.Debug("Looking for " + os.path.join(path, root_file + '.chapters.xml'))

        if not os.path.isfile(os.path.join(path, root_file + '.chapters.xml')):
            return

        data = Core.storage.load(os.path.join(path, root_file + '.chapters.xml'))
        xml_data = XML.ElementFromString(data)

        metadata.chapters.clear()

        for match in xml_data.xpath('//cg:chapterInfo', namespaces={'cg': 'http://jvance.com/2008/ChapterGrabber'}):
            chapters = match.find('cg:chapters', namespaces={'cg': 'http://jvance.com/2008/ChapterGrabber'})
            source   = match.find('cg:source', namespaces={'cg': 'http://jvance.com/2008/ChapterGrabber'})

            duration = None
            if source is not None:
                durationText = source.findtext('cg:duration', namespaces={'cg': 'http://jvance.com/2008/ChapterGrabber'})
                duration = self.convertTime(durationText)
            
            if duration == None:
                duration = int(long(getattr(media.items[0].parts[0], 'duration')))
           
            lastChapter = None
            for chapter in chapters.xpath('cg:chapter', namespaces={'cg': 'http://jvance.com/2008/ChapterGrabber'}):
                time = self.convertTime(chapter.get('time'))
                name = chapter.get('name').strip()

                if lastChapter != None:
                    lastChapter.end_time_offset = time

                chapter = metadata.chapters.new()
                chapter.title = name
                chapter.start_time_offset = time

                lastChapter = chapter

            if lastChapter != None and duration != None:
                lastChapter.end_time_offset = duration

            Log.Debug('Added %d chapters.' % len(metadata.chapters))
            for chapter in metadata.chapters:
                Log.Debug('%s %d %d', chapter.title, chapter.start_time_offset / 1000, chapter.end_time_offset / 1000)
