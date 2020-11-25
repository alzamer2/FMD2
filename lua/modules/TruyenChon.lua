function Init()
	function AddWebsiteModule(id, name, url, category)
		local m = NewWebsiteModule()
		m.ID                       = id
		m.Name                     = name
		m.RootURL                  = url
		m.Category                 = category
		m.SortedList               = true
		m.OnGetInfo                = 'GetInfo'
		m.OnGetPageNumber          = 'GetPageNumber'
		m.OnBeforeDownloadImage    = 'BeforeDownloadImage'
		m.OnGetNameAndLink         = 'GetNameAndLink'
		m.OnGetDirectoryPageNumber = 'GetDirectoryPageNumber'
	end
	local cat = 'Vietnamese'
	AddWebsiteModule('ef7f922bd45f4f9d9c559a55f987004d', 'TruyenChon', 'http://truyenchon.com', cat)
	AddWebsiteModule('567780dbaa3149e7ad698f11ce68ea9b', 'NetTruyen', 'http://www.nettruyen.com', cat)
	AddWebsiteModule('d25308907620480496bd73f50451d67f', 'NhatTruyen', 'http://nhattruyen.com', cat)

	cat = 'English'
	AddWebsiteModule('d2f24dec90e841b1aab4bea145ffb638', 'MangaNT', 'https://mangant.com', cat)
	AddWebsiteModule('76b33c241c0d44a6b4a5b8dd86ec7750', 'ManhuaES', 'https://manhuaes.com', cat)
end

local dirurl = {
	['ef7f922bd45f4f9d9c559a55f987004d'] = '/the-loai?status=-1&sort=15&page=%s', -- truyenchon
	['567780dbaa3149e7ad698f11ce68ea9b'] = '/tim-truyen?status=-1&sort=15&page=%s', -- nettruyen
	['d2f24dec90e841b1aab4bea145ffb638'] = '/genres?status=-1&sort=15&page=%s', -- mangant
	['d25308907620480496bd73f50451d67f'] = '/the-loai?status=-1&sort=15&page=%s', -- nhattruyen
	['76b33c241c0d44a6b4a5b8dd86ec7750'] = '/category-comics/manga/page/%s' -- manhuaes
}

function GetInfo()
	MANGAINFO.URL = MaybeFillHost(MODULE.RootURL, URL)
	if HTTP.GET(MANGAINFO.URL) then
		local x = CreateTXQuery(HTTP.Document)
		MANGAINFO.Title     = x.XPathString('//h1[@class="title-detail"]')
		MANGAINFO.CoverLink = MaybeFillHost(MODULE.RootURL, x.XPathString('//div[contains(@class, "col-image")]/img/@src'))
		MANGAINFO.Status    = MangaInfoStatusIfPos(x.XPathString('//li[contains(@class, "status")]/p[2]'), 'Đang tiến hành', 'Hoàn thành')
		if MANGAINFO.Status == '' then
			MANGAINFO.Status = MangaInfoStatusIfPos(x.XPathString('//p[contains(., "status")]/following-sibling::p'))
		end
		MANGAINFO.Authors   = x.XPathString('//li[contains(@class, "author")]/p[2]')
		if MANGAINFO.Authors == '' then
			MANGAINFO.Authors = x.XPathStringAll('//p[contains(., "Author(s)")]/following-sibling::p/a')
		end
		MANGAINFO.Artists   = x.XPathString('//h4[starts-with(./label,"Artista")]/substring-after(.,":")')
		MANGAINFO.Genres    = x.XPathStringAll('//li[contains(@class, "kind")]/p[2]/a')
		MANGAINFO.Summary   = x.XPathString('//div[@class="detail-content"]/p')

		x.XPathHREFAll('//div[@class="list-chapter"]//ul/li/div[contains(@class, "chapter")]/a', MANGAINFO.ChapterLinks, MANGAINFO.ChapterNames)
		MANGAINFO.ChapterLinks.Reverse(); MANGAINFO.ChapterNames.Reverse()
		return no_error
	else
		return net_problem
	end
end

function GetPageNumber()
	TASK.PageLinks.Clear()
	if HTTP.GET(MaybeFillHost(MODULE.RootURL, URL)) then
		local x = CreateTXQuery(HTTP.Document)
		if MODULE.ID == '76b33c241c0d44a6b4a5b8dd86ec7750' then -- manhuaes
			x.XPathStringAll('//div[contains(@class,"reading-detail")]/*[not(contains(@class,"mrt5"))]//img/@data-src', TASK.PageLinks)
		else
			x.XPathStringAll('//div[@class="page-chapter"]/img/@data-original', TASK.PageLinks)
		end
	else
		return false
	end
	return true
end

function BeforeDownloadImage()
	HTTP.Headers.Values['Referer'] = ' ' .. MaybeFillHost(MODULE.RootURL, TASK.ChapterLinks[TASK.CurrentDownloadChapterPtr])
	return true
end

function GetNameAndLink()
	if HTTP.GET(MODULE.RootURL .. dirurl[MODULE.ID]:format((URL + 1))) then
		local x = CreateTXQuery(HTTP.Document)
		x.XPathHREFAll('//div[@class="item"]//h3/a', LINKS, NAMES)
		if LINKS.Count == 0 then x.XPathHREFAll('//div[@class="overlay"]/a',LINKS,NAMES) end
		return no_error
	else
		return net_problem
	end
end

function GetDirectoryPageNumber()
	if HTTP.GET(MODULE.RootURL .. dirurl[MODULE.ID]:format('1')) then
		local x = CreateTXQuery(HTTP.Document)
		local s = x.XPathString('//ul[@class="pagination"]/li[last()]/a/@href')
		PAGENUMBER = tonumber(s:match('&page=(%d+)')) or 1
		return no_error
	else
		return net_problem
	end
end