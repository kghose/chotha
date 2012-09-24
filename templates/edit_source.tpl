<!-- Allows us to edit a source -->

<div class='content newentry'>
<form action="/refetchsource" method="POST">
Refetch source <input type="text" name="query" size='30' title="Enter pubmed query and hit enter to refetch the bibliographic data">
<input type="hidden" name="id" value={{source['id']}}>
<input type="hidden" name="nid" value={{source['nid']}}>
</form>
</div>

<form action="/savesource" method="POST">

<textarea class="filldiv" name="bibtex" rows="20" title="Bibtex representation of source">{{source_bibtex}}</textarea>
<input type="hidden" name="id" value={{source['id']}}>
<input type="hidden" name="nid" value={{source['nid']}}>
<input type="submit" name="save" value="save">
</form>