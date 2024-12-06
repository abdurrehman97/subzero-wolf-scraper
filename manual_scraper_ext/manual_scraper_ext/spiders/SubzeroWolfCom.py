import scrapy
import re


class SubzeroWolfComSpider(scrapy.Spider):
    name = 'subzero-wolf.com'
    start_urls = [
        "https://www.subzero-wolf.com/cove/configurator#sort=%40displayorder%20descending&numberOfResults=21",
        "https://www.subzero-wolf.com/sub-zero/configurator#sort=%40displayorder%20descending&numberOfResults=21",
        "https://www.subzero-wolf.com/wolf/configurator#sort=%40displayorder%20descending&numberOfResults=21"
    ]

    def parse(self, response, **kwargs):
        if "cove" in response.url:
            return self.handling_api(response, brand="cove")
        elif "sub-zero" in response.url:
            return self.handling_api(response, brand="sub-zero")
        elif "wolf" in response.url:
            return self.handling_api(response, brand="wolf")

    def extract_attributes(self, response, brand):
        model = response.css("#productNoValue::text").get()
        product = response.css(".product-title-heading::text").get()
        thumb = response.css("#productHeaderImg img::attr(src)").get()
        type_ = response.xpath('.//div[contains(@class, "tab-pane")]//li/a[contains(text(), "Use and Care Guide")]/text()').get()
        type_ = re.search(r"(Use and Care Guide)", type_)
        type_ = type_.group(0) if type_ else None
        file_urls = response.xpath('.//a[contains(text(), "Use and Care Guide")]/@href').get()
        brand_name = response.css('span[itemprop="name"]::text').get()
        language = response.css('html.non-touch::attr(lang)').get()
        if thumb:
            thumb = f"https://www.subzero-wolf.com/trade-resources/product-specifications/product-specifications-detail{thumb}"
        if file_urls:
            file_urls = f'https://www.subzero-wolf.com/{file_urls}'

        yield {
            "model": model if model else None,
            "model_2": '',
            "brand": brand_name if brand_name else None,
            "product": product if product else None,
            "product_parent": '',
            "product_lang": language.split('-')[0],
            "file_urls": file_urls,
            "type": type_,
            "url": response.url,
            "thumb": thumb,
            "source": "Sub-Zero, Wolf, and Cove | Kitchen Appliances that Inspire",
            "brand_category": brand
        }

    def parsing_api_response(self, response, brand):
        data = response.json()
        if 'results' in data:
            res = data['results']
            for item in res:
                yield scrapy.Request(
                    url=item['printableUri'],
                    callback=self.extract_attributes,
                    cb_kwargs={'brand': brand},
                    cookies={'CheckCountry': 'False'}
                )
        else:
            self.log(f"No results found in API response for brand: {brand}")

    def handling_api(self, response, brand):
        sitecoreItemUri = response.css(".CoveoForSitecoreContext::attr(data-sc-item-uri)").get()
        siteName = response.css(".CoveoForSitecoreContext::attr(data-sc-site-name)").get()

        # Select the API based on the site region
        api = "https://ca.subzero-wolf.com/coveo/rest/search/v2" if siteName == 'Canada' else "https://www.subzero-wolf.com/coveo/rest/search/v2"

        # Build payload based on the brand
        if brand == "cove":
            payload = {
                'aq': '(NOT @z95xtemplate==(ADB6CA4F03EF4F47B9AC9CE2BA53FF97,FE5DD82648C6436DB87A7C4210C7413B)) ((@issearchable==true) (@brand==cove) (@productstatus==active))',
                'cq': '(@z95xlanguage=="en-US") (@z95xlatestversion==1) (@source=="Coveo_web_index - s10.subzero.com")',
            }
        elif brand == "sub-zero":
            payload = {
                'aq': '(NOT @z95xtemplate==(ADB6CA4F03EF4F47B9AC9CE2BA53FF97,FE5DD82648C6436DB87A7C4210C7413B)) ((@issearchable==true) (@brand=="sub-zero") (@productstatus==active))',
                'cq': '(@z95xlanguage=="en-US") (@z95xlatestversion==1) (@source=="Coveo_web_index - s10.subzero.com")',
                'numberOfResults': '100'
            }
        elif brand == "wolf":
            payload = {
                'aq': '(@wolfcategory == "Ranges") (NOT @z95xtemplate==(ADB6CA4F03EF4F47B9AC9CE2BA53FF97,FE5DD82648C6436DB87A7C4210C7413B)) ((@issearchable==true) (@brand==wolf) (@productstatus==active))',
                'cq': '(@z95xlanguage=="en-US") (@z95xlatestversion==1) (@source=="Coveo_web_index - s10.subzero.com")',
                'numberOfResults': '100'
            }

        yield scrapy.FormRequest(
            url=api,
            callback=self.parsing_api_response,
            method='POST',
            formdata=payload,
            cb_kwargs={'brand': brand},
            headers={
                "Accept": "*/*",
                "Content-Type": 'application/x-www-form-urlencoded; charset="UTF-8"'
            },
            meta={'sitecoreItemUri': sitecoreItemUri, 'siteName': siteName}
        )
