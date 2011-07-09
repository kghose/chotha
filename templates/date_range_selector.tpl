<!-- This gadget allows us to select date ranges -->
%import urllib, datetime

%#current_start_date = datetime.date(2011,01,01)
%#current_end_date = datetime.date(2011,12,31)
<table width="100">
%for year in range(drd['end year'],drd['start year'],-1):
<tr>
<td>{{year}}</td>
%for month in range(1,13):
%this_date = datetime.date(year=year,month=month,day=1)
%start_date = current_start_date
%end_date = current_end_date

%color = 'white'
%if this_date > current_end_date:
%  start_date = current_start_date
%  end_date = this_date
%  title = 'Set as end'
%elif this_date < current_start_date:
%  start_date = this_date
%  end_date = current_end_date
%  title = 'Set as start'
%else: #Means the date is in the middle
%  color = 'black'
%	 if current_end_date - this_date > this_date - current_start_date:
%    start_date = this_date
%    title = 'Set as start' 
%  else:
%    end_date = this_date
%    title = 'Set as end'
%  end
%end

%query = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('start_date',start_date), ('end_date',end_date)]
<td bgcolor="{{color}}" color="{{color}}"><a href="/?{{urllib.urlencode(query)}}" title="{{title}}">O</a></td>
%end
</tr>
%end
</table>