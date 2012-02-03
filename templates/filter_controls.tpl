<!-- Pass in current limit, offset and total rows found -->
%import urllib
%cskeyword_list = filter_data['cskeyword_list']
%search_text = filter_data['search_text']
%current_limit = filter_data['limit']
%candidate_keywords = filter_data['candidate_keywords']
%total_found = filter_data['total_found']
%total_shown = filter_data['total_shown']
%limit = filter_data['limit']
%offset = filter_data['offset']

%query = [('cskeyword_list', cskeyword_list), \
%         ('limit',limit), ('offset',0)]
<form action="/?{{urllib.urlencode(query)}}" method="GET">
<input class="filldiv" type="text" size=20 name="search_text" title="Search" value="{{search_text}}">
<!-- These need to be passed too, secretly -->
<input type="hidden" name="cskeyword_list" value="{{cskeyword_list}}">
<input type="hidden" name="limit" value="{{limit}}">
<input type="hidden" name="offset" value=0>
</form>
%if cskeyword_list != '':
{{'+' + cskeyword_list}}
%query = [('cskeyword_list',cskeyword_list)]
(<a href="/options/setdesktop/?{{urllib.urlencode(query)}}" title="Set this keyword combination as desktop">Set as desktop</a>)
%end
<p><b>{{total_found}} found</b></p>

%pre = cskeyword_list + ',' if cskeyword_list != '' else ''
%for keyword in candidate_keywords:
%query = [('cskeyword_list',pre.encode('utf-8') + keyword['name'].encode('utf-8')), \
%         ('search_text', search_text.encode('utf-8')), \
%         ('limit',current_limit), ('offset',0)]
<a href="/?{{urllib.urlencode(query)}}">{{keyword['name']}}</a><br/>
%end
