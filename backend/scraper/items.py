import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def clean_text(value):
    """Clean and normalize text content"""
    if value:
        return value.strip().replace('\n', ' ').replace('\t', ' ')
    return value


def parse_deal_value(value):
    """Extract numeric deal value from text"""
    if not value:
        return None
    
    import re
    # Extract numbers and units (billion, million)
    match = re.search(r'[\$]?(\d+(?:\.\d+)?)\s*(billion|million|b|m)', value.lower())
    if match:
        number = float(match.group(1))
        unit = match.group(2).lower()
        if unit in ['billion', 'b']:
            return number * 1000000000
        elif unit in ['million', 'm']:
            return number * 1000000
    return None


class NewsArticleItem(scrapy.Item):
    """News article item for M&A news scraping"""
    
    # Article metadata
    url = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    content = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=Join(' ')
    )
    summary = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    
    # Publication details
    source = scrapy.Field(output_processor=TakeFirst())
    author = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    published_date = scrapy.Field(output_processor=TakeFirst())
    scraped_date = scrapy.Field(output_processor=TakeFirst())
    
    # Content categorization
    category = scrapy.Field(output_processor=TakeFirst())
    tags = scrapy.Field()
    
    # Article metrics
    word_count = scrapy.Field(output_processor=TakeFirst())
    reading_time = scrapy.Field(output_processor=TakeFirst())


class DealItem(scrapy.Item):
    """M&A deal item extracted from news articles"""
    
    # Deal identification
    deal_id = scrapy.Field(output_processor=TakeFirst())
    deal_type = scrapy.Field(output_processor=TakeFirst())  # merger, acquisition, ipo, etc.
    deal_status = scrapy.Field(output_processor=TakeFirst())  # announced, pending, completed, canceled
    
    # Companies involved
    target_company = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    acquirer_company = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Financial details
    deal_value = scrapy.Field(
        input_processor=MapCompose(parse_deal_value),
        output_processor=TakeFirst()
    )
    deal_value_currency = scrapy.Field(output_processor=TakeFirst())
    enterprise_value = scrapy.Field(
        input_processor=MapCompose(parse_deal_value),
        output_processor=TakeFirst()
    )
    
    # Deal characteristics
    industry_sector = scrapy.Field(output_processor=TakeFirst())
    geographic_region = scrapy.Field(output_processor=TakeFirst())
    deal_structure = scrapy.Field(output_processor=TakeFirst())  # cash, stock, mixed
    
    # Timeline
    announcement_date = scrapy.Field(output_processor=TakeFirst())
    expected_completion_date = scrapy.Field(output_processor=TakeFirst())
    actual_completion_date = scrapy.Field(output_processor=TakeFirst())
    
    # Advisors and participants
    financial_advisors = scrapy.Field()
    legal_advisors = scrapy.Field()
    
    # Data quality and source
    source_url = scrapy.Field(output_processor=TakeFirst())
    source_article_id = scrapy.Field(output_processor=TakeFirst())
    confidence_score = scrapy.Field(output_processor=TakeFirst())
    extraction_method = scrapy.Field(output_processor=TakeFirst())  # manual, ai, structured
    
    # Metadata
    created_date = scrapy.Field(output_processor=TakeFirst())
    last_updated = scrapy.Field(output_processor=TakeFirst())


class CompanyItem(scrapy.Item):
    """Company information item"""
    
    # Basic company info
    company_id = scrapy.Field(output_processor=TakeFirst())
    company_name = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    ticker_symbol = scrapy.Field(output_processor=TakeFirst())
    exchange = scrapy.Field(output_processor=TakeFirst())
    
    # Company details
    industry = scrapy.Field(output_processor=TakeFirst())
    sector = scrapy.Field(output_processor=TakeFirst())
    market_cap = scrapy.Field(output_processor=TakeFirst())
    headquarters = scrapy.Field(output_processor=TakeFirst())
    
    # Financial metrics
    revenue = scrapy.Field(output_processor=TakeFirst())
    employees = scrapy.Field(output_processor=TakeFirst())
    founded_year = scrapy.Field(output_processor=TakeFirst())
    
    # Metadata
    data_source = scrapy.Field(output_processor=TakeFirst())
    last_updated = scrapy.Field(output_processor=TakeFirst())


class RSSFeedItem(scrapy.Item):
    """RSS feed item for structured news feeds"""
    
    title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    link = scrapy.Field(output_processor=TakeFirst())
    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    published_date = scrapy.Field(output_processor=TakeFirst())
    source = scrapy.Field(output_processor=TakeFirst())
    guid = scrapy.Field(output_processor=TakeFirst())
    category = scrapy.Field(output_processor=TakeFirst())
    author = scrapy.Field(output_processor=TakeFirst())