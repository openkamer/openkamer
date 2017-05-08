from haystack.forms import SearchForm
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
        
class FacetedSearchForm(SearchForm):
    def __init__(self, *args, **kwargs):
        self.selected_facets = kwargs.pop("selected_facets", [])
        super(FacetedSearchForm, self).__init__(*args, **kwargs)

    def search(self):
        sqs = super(FacetedSearchForm, self).search()

        for facet in self.selected_facets:
            if ":" not in facet:
                continue


            field, value = facet.split(":", 1)
                                                      
                                                    
            if value:
                if field=='date':
                    lower,upper = value.split("_TO_",1)
                    string = u'%s:["%s" TO "%s"]' % (field, sqs.query.clean(lower), sqs.query.clean(upper))                    
                    sqs = sqs.narrow(string)    
                else:
                    sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))

        return sqs