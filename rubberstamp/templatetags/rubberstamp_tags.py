from django import template


register = template.Library()


class IfPermsNode(template.Node):
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.contents.split()
        do_nodelist = parser.parse(("endifperms",))
        parser.delete_first_token()
        return cls(bits[1], bits[2], bits[3], do_nodelist=do_nodelist)
    
    def __init__(self, user, perm, obj=None, as_var=None, do_nodelist=None):
        self.user_var = template.Variable(user)
        self.perm_var = template.Variable(perm)
        self.obj_var = template.Variable(obj)
        self.as_var = as_var # not supported yet
        self.do_nodelist = do_nodelist
    
    def render(self, context):
        
        user = self.user_var.resolve(context)
        perm = self.perm_var.resolve(context)
        obj = self.obj_var.resolve(context)
        
        if self.do_nodelist is not None:
            if user.has_perm(perm, obj=obj):
                output = self.do_nodelist.render(context)
            else:
                output = ""
        return output


@register.tag
def ifperms(parser, token):
    return IfPermsNode.handle_token(parser, token)
