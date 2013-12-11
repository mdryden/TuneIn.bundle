from lxml import etree

MUSIC_PREFIX = "/music/tunein"
NAME = "TuneIn Radio"

ART = "art-default.png"
ICON = "icon-default.png"


def Start():

	# Initialize the plugin
	Plugin.AddPrefixHandler(MUSIC_PREFIX, MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("List", viewMode = "InfoList", mediaType = "items")

	ObjectContainer.title1 = NAME
	
	Log.Debug("Plugin Start")
	

def MainMenu():
	Log.Debug("MainMenu()")
	
	return LinkMenu("http://feed.tunein.com/Browse.ashx", L("MainMenuTitle"))
	
def LinkMenu(url, title):
	dir = ObjectContainer(title2 = title)
	
	data = XML.ElementFromURL(url, cacheTime=0)
	Log.Debug("data: " + str(data))
				
	for item in data.xpath("//body/outline[@type='link']"):
		text = item.xpath("./@text")[0]
		url = item.xpath("./@URL")[0]
		
		# links call back to this same menu
		dir.add(DirectoryObject(
			key = Callback(LinkMenu, url=url, title=text), # call back to itself makes it go nowhere - in some clients anyway.
			title = text
		))
		
	for item in data.xpath("//body/outline[@text]/outline[@type='audio']"):		
		dir.add(CreateTrackObjectFromElement(item))
	
	return dir
	
def CreateTrackObjectFromElement(item):
	text = item.xpath("./@text")[0]
	url = item.xpath("./@URL")[0]
	id = item.xpath("./@guide_id")[0]
	formats = item.xpath("./@formats")[0]
	try: #playing might not be available
		playing = item.xpath("./@playing")[0]
	except:
		playing = ""
		
	image = item.xpath("./@image")[0]
	
	return TrackObject(
		key = Callback(PlayAudio, url=url),
		rating_key = url,
		title = text,
		artist = playing,
		thumb = image
	)
	

def PlayAudio(url):
	
	stream_url = GetStreamUrl(url)
	
	Log.Debug("Redirecting to " + stream_url)
	return Redirect(stream_url)
	
def GetStreamUrl(url):
	content = HTTP.Request(url, cacheTime=0).content
	
	Log.Debug(content)
	
	if content.find(".pls") > -1 or content.find(".asx") > -1:
		return GetUrlFromPlayList(content, "File1=")
	elif content.find(".asf"):
		return GetUrlFromPlayList(content, "Ref1=")
	elif content.find(".m3u"):
		return GetUrlFromPlayList(content)
	else:
		# some contain a non-identifiable url which redirects to another
		# find the first http link and follow it
		RE_HTTP = Regex('(http?://.+)')	
		url = RE_HTTP.search(content)
		if url:
			return GetStreamUrl(url)
		
	#shouldn't get here
	raise Ex.MediaNotAvailable
	
	
def GetUrlFromPlayList(content, prefix = ""):
	RE_HTTP = Regex('(http?://.+)')	
	file_url = RE_HTTP.search(content)
	
	if file_url:
		stream_content = HTTP.Request(file_url.group(0), cacheTime=0).content
		Log.Debug("stream_content = " + stream_content)
		
		RE_FILE = Regex(prefix + '(http?://.+)')
		stream_url = RE_FILE.search(stream_content)
		
		if stream_url:
			#Log.Debug(stream_url.group(1))
			return stream_url.group(1)
	
	#shoudln't make it here
	raise Ex.MediaNotAvailable
