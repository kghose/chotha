<!-- This gadget allows us to select date ranges -->

%import urllib, datetime

<table>
%for year in range(drd['end year'],drd['start year']-1,-1):
<tr>
<td>{{year}}</td>
%for month in range(1,13):
%this_date = datetime.date(year=year,month=month,day=1)

%color = 'white'
%if (this_date >= current_start_date) & (this_date <= current_end_date):
%  color = 'black'
%end

%query1 = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',this_date), ('end_date',current_end_date)]

%query2 = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',current_start_date), ('end_date',this_date)]

<td bgcolor="{{color}}" nowrap color="{{color}}">
<a href="/?{{urllib.urlencode(query1)}}">[</a>
<a href="/?{{urllib.urlencode(query2)}}">]</a>
</td>
%end
</tr>
%end
</table>
