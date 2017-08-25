import os
import logging
from ZenPacks.zenoss.ZenPackLib import zenpacklib


CFG = zenpacklib.load_yaml([os.path.join(os.path.dirname(__file__), "zenpack.yaml")], verbose=False, level=30)
schema = CFG.zenpack_module.schema


from Products import Zuul
from Products.ZenUtils.Utils import monkeypatch
from Products.ZenUtils.zencatalog import reindex_catalog
from Products.Zuul.routers.report import ReportRouter


ZEN_ROLE = 'ZenReportUser'
LOG = logging.getLogger('Zen.ReportUserControl')


class ZenPack(schema.ZenPack):
    def install(self, app):
        super(ZenPack, self).install(app)
        self.installRole(app.zport, ZEN_ROLE)

        if not getattr(self, 'prevZenPackVersion', None):
            #update catalog to index new role
            globalCat = app.getPhysicalRoot().zport.global_catalog
            reindex_catalog(globalCat, permissionsOnly=True, printProgress=True, commit=False)

        LOG.info('Disabling Reports for ZenUser')
        app.zport.dmd.Reports.manage_permission(
            'View',
            ['ZenManager', 'Manager', 'ZenReportUser'], acquire=False
        )


    def remove(self, app, leaveObjects=False):
        super(ZenPack, self).remove(app, leaveObjects=leaveObjects)
        if not leaveObjects:
            self.removeRole(app.zport, ZEN_ROLE)
            LOG.info('Enabling Reports for ZenUser')
            app.zport.dmd.Reports.manage_permission(
                'View',
                ['ZenManager', 'Manager', 'ZenUser'], acquire=False
            )


    def installRole(self, zport, role):
        # Add the role
        if role not in zport.__ac_roles__:
            zport.__ac_roles__ += (role,)
            zport.acl_users.roleManager.addRole(role)

        # Allow ZenOperator basic view permissions
        zport.manage_role(role, [ZEN_ROLE])

    def removeRole(self, zport, role):
        currentRoles = zport.__ac_roles__
        if role in currentRoles:
            zport.__ac_roles__ = [ r for r in currentRoles if r != role ]
            zport.acl_users.roleManager.removeRole(role)


#@monkeypatch('Products.Zuul.routers.report.ReportRouter')
#def asyncGetTree(self, id=None):
#    if Zuul.checkPermission('ZenReportUser', self.context):
#        return super(ReportRouter, self).asyncGetTree(id, additionalKeys=self.keys)
#    else:
#        return []

