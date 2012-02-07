<!-- Pass in current limit, offset and total rows found -->
%import urllib
%cskeyword_list = filter_data['cskeyword_list']
%search_text = filter_data['search_text']
%current_limit = filter_data['limit']
%current_offset = filter_data['offset']
%total_found = filter_data['total_found']

{{total_found}}<hr/>


%for limit in [10,100,1000]:

%query = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('limit',limit), ('offset',0)]
%if current_limit >= limit and current_limit < limit+1:
%str="<b>%d</b>" %(limit)
%else:
%str="%d" %(limit)
%end
<a href="/?{{urllib.urlencode(query)}}">{{!str}}</a></br>

%end
<hr/>

%offset = 0
%page = 1
%while offset < total_found:
%query = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('limit',current_limit), ('offset',offset)]
%if current_offset >= offset and current_offset < offset+1:
%str="<b>%d</b>" %(page)
%else:
%str="%d" %(page)
%end
<a href="/?{{urllib.urlencode(query)}}">{{!str}}</a></br>
%offset += current_limit
%page +=1
%end
