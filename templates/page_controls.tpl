<!-- Pass in current limit, offset and total rows found -->
%import urllib
%cskeyword_list = filter_data['cskeyword_list']
%search_text = filter_data['search_text']
%current_limit = filter_data['limit']
%current_offset = filter_data['offset']
%total_found = filter_data['total_found']

<p>
%for limit in [10,100,1000]:
%query = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('limit',limit), ('offset',0)]
%if current_limit >= limit and current_limit < limit+1:
<a href="/?{{urllib.urlencode(query)}}"><b>{{limit}}</b></a>
%else:
<a href="/?{{urllib.urlencode(query)}}">{{limit}}</a>
%end
%end
</p>

<p>
%offset = 0
%page = 1
%while offset < total_found:
%query = [('cskeyword_list', cskeyword_list), \
%					('search_text', search_text), \
%         ('limit',current_limit), ('offset',offset)]
%if current_offset >= offset and current_offset < offset+1:
<a href="/?{{urllib.urlencode(query)}}"><b>{{page}}</b></a>
%else:
<a href="/?{{urllib.urlencode(query)}}">{{page}}</a>
%end
%offset += current_limit
%page +=1
%end
</p>