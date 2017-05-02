class Facet(object):
    def __init__(self,field,label=None):
        self.field = field
        self.label = label if label else field
        self.list_of_facetitems = []
        
    def __str__(self):
        return self.field
        
class FacetItem(object):
    def __init__(self,value,count,base_url='',is_selected=False):
        self.value = value
        self.count = count
        self.base_url = base_url
        self.facet= None
        self.is_selected=is_selected
    
    @property
    def url(self):
        return self.build_url()
        
    def build_url(self):
        url = self.base_url
        
        if not self.is_selected:
            url = url + "&selected_facets=" +self.facet.field +":" +self.value
        else:
            url = url.replace("&selected_facets=" +self.facet.field +":" +(self.value), "")
        return url
    
    def __str__(self):
        return self.value, self.count