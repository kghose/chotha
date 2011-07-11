<!-- This gadget allows us to select date ranges -->

%import urllib, datetime
%from calendar import monthrange

%sel_year = end_date.year
%sel_month1 = end_date.month
%sel_month2 = start_date.month

<!-- years -->
<div class="date-column">
<span>Year</span><br/>
%this_end_date = datetime.date(year=daterangedata['end year'],month=12,day=31)
%this_start_date = datetime.date(year=daterangedata['start year'],month=1,day=1)
%query1 = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',this_start_date), ('end_date',this_end_date)]
<a href="/?{{urllib.urlencode(query1)}}">All</a></br>

%for year in range(daterangedata['end year'],daterangedata['start year']-1,-1):

%this_end_date = datetime.date(year=year,month=12,day=31)
%this_start_date = datetime.date(year=year,month=1,day=1)
%query1 = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',this_start_date), ('end_date',this_end_date)]

%if year == sel_year:
<a href="/?{{urllib.urlencode(query1)}}"><b>{{year}}</b></a></br>
%else:
<a href="/?{{urllib.urlencode(query1)}}">{{year}}</a></br>
%end

%end
</div>
<!-- years -->

<!-- months -->
<div class="date-column">
<span>Month</span><br/>
%for month in range(1,13):

%mdays = monthrange(sel_year,month)
%this_end_date = datetime.date(year=sel_year,month=month,day=mdays[1])
%this_start_date = datetime.date(year=sel_year,month=month,day=1)
%query1 = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',this_start_date), ('end_date',this_end_date)]

%if month >= sel_month2 and month <= sel_month1:
<a href="/?{{urllib.urlencode(query1)}}"><b>{{month}}</b></a></br>
%else:
<a href="/?{{urllib.urlencode(query1)}}">{{month}}</a></br>
%end

%end
</div>
<!-- months -->
