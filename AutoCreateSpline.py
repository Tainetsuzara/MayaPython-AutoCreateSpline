#!/usr/bin/env python
# -*- coding: utf_8 -*-
#________________________________________________________
# create by hisakazu aoki
#------ how to use ------
#   select 2 joint to joint chane start end 
#   create spline ik rig

#------ about stratch ------
#   created route rig has attributes related to stretching
#________________________________________________________

from maya.api.OpenMaya import MVector, MMatrix, MPoint
import maya.cmds as mc

class CreateAutoSplineClass():
	def __init__(self):
		print("I hope it goes well")
		

	#UIを作成します
	def CreateUI(self, *args):
		if mc.window('CreateAutoSplineWindow', q=True, ex=True) == True:
			mc.deleteUI('CreateAutoSplineWindow')
			
		mc.window('CreateAutoSplineWindow',title='CreateAutoSpline')
		mc.paneLayout('CreateSplineIkMainColumn', p='CreateAutoSplineWindow',cn='single')
		mc.button('CreateSplineIk', p='CreateSplineIkMainColumn', c=self.CheckSelItems)
		mc.showWindow()
	#スプラインikを作成するための条件を満たしているか調べます
	def CheckSelItems(self, *args):
		SelJoint = mc.ls(sl=True,long=True)
		
		StartJoint = SelJoint[0].split('|')
		Rip = SelJoint[-1].split('|')
		TrgJointOligine = [a for a in Rip if a != '']
		
		if SelJoint == []:
			mc.confirmDialog(m='Please specify the start and end points of the joint chain')
			
		elif len(SelJoint) != 2:
			mc.confirmDialog(m='Please specify the start and end points of the joint chain')
			
		elif len(TrgJointOligine) < 4:
			mc.confirmDialog(m='Select the start and end points of a joint chain of 4 or more')
			
		elif StartJoint[-1] not in TrgJointOligine:
			Message_1 ='The long name of the end point did not include the name of the joint of the start point.\n'
			Message_2 ='You may not have selected a chain.\n'
			Message_3 ='Please double check the selected joint.'
			Message = Message_1 + Message_2 + Message_3
			mc.confirmDialog(m=Message)
		else:
			self.CreateAutoSpline()


	def CreateAutoSpline(self, *args):
		#セレクトジョイントの取得(ロングネームで取得し、最後のジョイントの名前に対象のジョイントの名前がすべて含まれる状態にする)
		SelJoint = mc.ls(sl=True,long=True)
		#確実に最後のジョイントを選択するため、順序を変更
		SelJoint.sort()
		#最後のジョイントは全てのジョイントの名前を分割し、ジョイントを取得
		Rip = SelJoint[-1].split('|')
		TrgJointOligine = [a for a in Rip if a != '']
		#全てのリスト内のジョイントをロングネームでリストします
		PreTrgJoint = []
		LongName = TrgJointOligine[0]
		for i in range(0,(len(TrgJointOligine)-1)):
			PreTrgJoint.append(LongName)	
			LongName = LongName + '|' + TrgJointOligine[i+1]	
			#print(TrgJoint)
		PreTrgJoint.append(SelJoint[-1])
		
		
		#ルートジョイントにルートが存在している場合、上記のスプリットではルートより上をリストしてしまう可能性があるので、
		#リストからルートジョイントより上のジョイントを除外するため、ルートジョイントの名前を取得します
		RootItemElements = [a for a in SelJoint[0].split('|') if a != '']
		RootLen = len(RootItemElements)
		#PreTrgJointのアイテムを｜で分割し、分割後の個数がRootLenより少ない場合、下記のリストにリストされません
		TrgJoint = []
		OrgJoint = []
		for i in PreTrgJoint:
			RipLen = len(i.split('|'))
			if RipLen >= RootLen:
				OrgJoint.append(i)
		#print ('OrgJoint : 下記のジョイントをオリジナルジョイントとしてリストしました')
		#print(OrgJoint)
		#ジョイントのロックを解放します
		for i in OrgJoint:
			mc.setAttr(i + ".tx", lock=False)
			mc.setAttr(i + ".ty", lock=False)
			mc.setAttr(i + ".tz", lock=False)
			mc.setAttr(i + ".rx", lock=False)
			mc.setAttr(i + ".ry", lock=False)
			mc.setAttr(i + ".rz", lock=False)
			mc.setAttr(i + ".sx", lock=False)
			mc.setAttr(i + ".sy", lock=False)
			mc.setAttr(i + ".sz", lock=False)
		
		
		#ジョイントを複製し、リストします
		num = len(mc.ls('AutoSplineIK_*'))
		DuplicateJont = mc.duplicate(OrgJoint, name=('AutoSplineIK_' + str(num + 1)),renameChildren=True,f=True)
		DeleteJoints = []
		for i in DuplicateJont:
			Rip = i.split('|')
			#print(Rip[-1])
			if 'AutoSplineIK_' not in Rip[-1]:
				DeleteJoints.append(i)
		
		TrgJoint = list(set(DuplicateJont) - set(DeleteJoints))
		TrgJoint = sorted(TrgJoint)
		TrgJoint = sorted(TrgJoint, key=len)
		if DeleteJoints != []:
			mc.delete(DeleteJoints)
		#print ('TrgJoint : 下記のジョイントをスプラインik用に複製しました')
		#print (TrgJoint)
		
		
		#groval groupを作成します
		num = len(mc.ls('AutoSplineRigGrobal_*')) + 1
		GrobalGrp = mc.group(em=True, n=('AutoSplineRigGrobal_' + str(num) + '_Grp'))
		SetupGrp = mc.group(em=True, n='Setup_Grp' , p=GrobalGrp)
		CtrlGrp = mc.group(em=True, n='Ctrl_Grp' , p=GrobalGrp)
		ClusterGrp = mc.group(em=True, n='Cluster_Grp' , p=SetupGrp)
		mc.setAttr(SetupGrp + '.v', False)
		#print('各要素を格納するgrpノードを作成しました')
		#print(GrobalGrp)
		#print(SetupGrp)
		#print(CtrlGrp)
		#print(ClusterGrp)
		
		#Curveのcvの位置情報を取得
		KnotPosList = []
		for i in TrgJoint:
			Matrix = MMatrix ( mc.xform( i, q=True, matrix=True, ws=True ) )
			Position = [Matrix[12],Matrix[13],Matrix[14]]
			KnotPosList.append(Position)
			#print(Position)	
			#print(KnotPosList)
		#print('下記のポイントをリストしました')
		#print(KnotPosList)
		
		#cvカーブを作成します
		SetNum = len(mc.ls('AutoSplineRigCurve_*', type='transform')) + 1
		TagCurve = mc.curve(p=KnotPosList,n=('AutoSplineRigCurve_' + str(SetNum)))
		
		#TagCurve = mc.curve(p=KnotPosList[0],n=('AutoSplineRigCurve_' + str(SetNum)))
		#for i in range(0,len(KnotPosList)-1):
		#	mc.curve(TagCurve, a=True, p=KnotPosList[i+1])
		
		#カーブシェイプをリネームします
		RenameShape = mc.listRelatives(TagCurve, s=True)
		CurveShape = mc.rename(RenameShape[0],(TagCurve + 'Shape'))
		mc.parent(TagCurve,SetupGrp)
		
		
		#ルートリグを作成します
		SetNum = len(mc.ls("AutoSplineRootRig_*_Ctrl", type='transform')) + 1
		AutoSplineRootRig = mc.curve(p=[(2, 0, 1),(2, 0, -1),(1,0,-1),(1,0,-2),(-1,0,-2),(-1,0,-1),(-2,0,-1),(-2,0,1),(-1,0,1),(-1,0,2),(1,0,2),(1,0,1),(2,0,1)], k=(0,1,2,3,4,5,6,7,8,9,10,11,12), n=("AutoSplineRootRig_" + str(SetNum)+ "_Ctrl") , d=1)
		AutoSplineRootRigGrp = (AutoSplineRootRig + '_Grp')
		mc.group( AutoSplineRootRig, n=AutoSplineRootRigGrp, p=CtrlGrp)
		
		#ルートリグにストレッチのon/offアトリを追加します
		mc.addAttr(AutoSplineRootRig, ln="________", at='enum',en="____:____:")
		mc.addAttr(AutoSplineRootRig, ln="Stratch", at='bool')
		mc.addAttr(AutoSplineRootRig, ln="Radius", at='bool')
		mc.addAttr(AutoSplineRootRig, ln="RadiusMagni", at='float')
		mc.setAttr(AutoSplineRootRig + '.________', e=True, keyable=True)
		mc.setAttr(AutoSplineRootRig + '.Stratch', e=True, keyable=True)
		mc.setAttr(AutoSplineRootRig + '.Radius', e=True, keyable=True)
		mc.setAttr(AutoSplineRootRig + '.RadiusMagni', e=True, keyable=True)
		mc.setAttr(AutoSplineRootRig + '.RadiusMagni', 1.0)
				
		#リグを作成し、依存関係を構築します
		IK_Rig_List = []
		IK_Rig_Grp = []
		num = len(mc.ls('AutoSplineRig_*', type='shape'))
		for e,v in enumerate(TrgJoint):
			IK_Rig = mc.circle(c=(0,0,0), nr=(0,1,0), sw=360, r=1, d=3, ut=0, tol=0.01, s=8, ch=1, n=('AutoSplineRig_' + str(num + 1 + e) + '_Ctrl'))
			IK_Rig_Grp.append(mc.group( IK_Rig, n=('AutoSplineRig_' + str(num + 1 + e) + '_Ctrl_Grp')))
			IK_Rig_List.append('AutoSplineRig_' + str(num + 1 + e) + '_Ctrl')
		mc.parent(IK_Rig_Grp, AutoSplineRootRig)
				
		#リグの形状が寝ているので起こします
		mc.setAttr(AutoSplineRootRigGrp + '.rz', 90 )
		mc.makeIdentity(AutoSplineRootRigGrp, apply=True, t=1, r=1, s=1, n=0, pn=1)
		mc.delete(AutoSplineRootRigGrp, constructionHistory = True)
		
		#ルートリグをジョイントにスナップします
		RootSnapConstraint = mc.parentConstraint(OrgJoint[0], AutoSplineRootRigGrp, n='RootSnaps_')
		mc.delete(RootSnapConstraint)
		
		#リグをジョイントにスナップします
		SnapConstraint = []
		for i in range(0,len(OrgJoint)):
			SnapConstraint.extend(mc.parentConstraint(OrgJoint[i], IK_Rig_Grp[i], n=('Snaps_' + str(i))))
		mc.delete(SnapConstraint)
				
		#スプラインikを設定します
		num = len(mc.ls('AutoSplineIKHandle_*'))
		SplineIKHandle = mc.ikHandle(sol='ikSplineSolver', ccv=False, pcv=False, sj=TrgJoint[0], ee=TrgJoint[-1], c=TagCurve, n=('AutoSplineIKHandle_' + str(num + 1)))
		#スプラインikのアドバンスドを設定
		mc.setAttr((SplineIKHandle[0] + ".dTwistControlEnable"), 1)
		mc.setAttr((SplineIKHandle[0] + ".dWorldUpType"), 4)
		mc.connectAttr((IK_Rig_List[0]+'.worldMatrix[0]'), (SplineIKHandle[0] + '.dWorldUpMatrix'), f=True)
		mc.connectAttr((IK_Rig_List[-1]+'.worldMatrix[0]'), (SplineIKHandle[0] + '.dWorldUpMatrixEnd'), f=True)
		
		mc.parent(SplineIKHandle[0], SetupGrp)
		
		
		#クラスタを作成します
		mc.select(TagCurve)
		mc.ClusterCurve()
		CluterList = list(set(mc.listConnections(CurveShape + 'Orig')))
		CluterList = sorted(CluterList)
		CluterList = sorted(CluterList, key=len)
		
		#クラスタをリネームします
		RenameCluster = []
		for i in CluterList:
			SetNum = len(mc.ls('AutoSplineCurveCluster_*', type='transform')) + 1
			RenameClusterHandle = mc.listConnections(i, s=True, type="transform")	
			RenameCluster.append(mc.rename(RenameClusterHandle[0],('AutoSplineCurveCluster_' + str(SetNum))))
		mc.parent(RenameCluster, ClusterGrp)
		
		#クラスタをコントロールリグでコンストレイントします
		SpClusterConst=[]
		for i in range(0,len(RenameCluster)):
			SpClusterConst.extend(mc.parentConstraint(IK_Rig_List[i], RenameCluster[i], mo=True, n=('AutoSpCluster_' + str(i))))
		
		mc.group(SpClusterConst, n='SpClusterConst_Grp', p=SetupGrp)
		
		
		
		#オリジナルジョイントをスプラインジョイントでコンストレインします
		ParentNum = len(mc.ls('AutoSplineJointConstraint_*'))
		ScaleNum = len(mc.ls('AutoSplineJointScaleConst_*'))
		ConstList = []
		ScaleConstList = []
		for i in range(0,len(OrgJoint)):
			ConstList.extend( mc.parentConstraint(TrgJoint[i], OrgJoint[i], mo=True, n=('AutoSplineJointConstraint_' + str(ParentNum + i))))
			mc.connectAttr((TrgJoint[i] + '.sx'), (OrgJoint[i] + '.sx'), force=True)
			mc.connectAttr((TrgJoint[i] + '.sy'), (OrgJoint[i] + '.sy'), force=True)
			mc.connectAttr((TrgJoint[i] + '.sz'), (OrgJoint[i] + '.sz'), force=True)
			#ScaleConstList.extend(  mc.scaleConstraint(TrgJoint[i], OrgJoint[i], mo=True, n=('AutoSplineJointScaleConst_' + str(ScaleNum + i))))
		mc.group(ConstList, n=('AutoSplineConstToOrgJoint_' + str(ParentNum + 1) + '_Grp'), p=SetupGrp)
		#mc.group(ScaleConstList, n=('AutoSplineJointScaleConst_' + str(ScaleNum + 1) + '_Grp'), p=SetupGrp)
		
		
		#ストレッチの設定を行います
		#カーブインフォを作成します
		num = len(mc.ls('AutoSplineCurtveInfo_*'))
		CurveInfo = mc.shadingNode('curveInfo',asUtility=True, n='AutoSplineCurtveInfo_' + str(num + 1))
		TagCurveShape = mc.listRelatives(TagCurve,s=True)
		mc.connectAttr( (TagCurveShape[0] + '.local'), (CurveInfo +'.inputCurve'), force=True)
		ArcLenParam = mc.getAttr(CurveInfo +'.arcLength')
		
		#ストレッチのコンディションノードを作成します
		num = len(mc.ls('ArcLenCondition_*'))
		ArcLenCondition = mc.shadingNode('condition', asUtility=True, n='ArcLenCondition_' + str(num + 1))
		mc.connectAttr((AutoSplineRootRig + '.Stratch'), (ArcLenCondition + '.firstTerm'), force=True)
		mc.connectAttr((CurveInfo +'.arcLength'), (ArcLenCondition + '.colorIfTrue.colorIfTrueR'), force=True)
		mc.setAttr(ArcLenCondition + '.operation', 2)
		mc.setAttr(ArcLenCondition + '.colorIfFalseR', ArcLenParam)
		
		
		#ストレッチの割合を計算する割り算を行うノードを作成します
		num = len(mc.ls('AutoSplineStratchDiv_*'))
		AutoSplineStratchDiv = mc.shadingNode('multiplyDivide',asUtility=True, n=('AutoSplineStratchDiv_' + str(num + 1)))
		mc.connectAttr((ArcLenCondition + '.outColorR'),(AutoSplineStratchDiv + '.input1X'), f=True)
		mc.setAttr(AutoSplineStratchDiv + '.input2X', ArcLenParam)
		mc.setAttr(AutoSplineStratchDiv + '.operation', 2)
		
		#ストレッチの割合からyzのスケールを算出するノードを作成します
		PowNum = len(mc.ls('AutoSplineStratchPow_*'))
		YZNum = len(mc.ls('AutoSplineStratchYZ_*'))
		AutoSplineStratchPow = mc.shadingNode('multiplyDivide',asUtility=True, n=('AutoSplineStratchPow_' + str(PowNum + 1)))
		AutoSplineStratchYZ = mc.shadingNode('multiplyDivide',asUtility=True, n=('AutoSplineStratchYZ_' + str(YZNum + 1)))
		
		#設定を行います
		mc.setAttr(AutoSplineStratchPow + '.input2X', 0.5)
		mc.setAttr(AutoSplineStratchPow + '.operation', 3)
		mc.setAttr(AutoSplineStratchYZ + '.input1X', 1.0)
		mc.setAttr(AutoSplineStratchYZ + '.operation', 2)
		mc.connectAttr((AutoSplineStratchPow + '.outputX'), (AutoSplineStratchYZ + '.input2X'), f=True)
		mc.connectAttr((AutoSplineStratchDiv + '.outputX'), (AutoSplineStratchPow + '.input1X'), f=True)
		
		#半径の収縮率を調整するmultiを作成します
		AutoSplineStratchRadius = mc.shadingNode('multiplyDivide',asUtility=True, n=('AutoSplineStratchRadius_' + str(YZNum + 1)))
		mc.setAttr(AutoSplineStratchRadius + '.operation', 1)
		mc.connectAttr((AutoSplineStratchYZ + '.outputX'), (AutoSplineStratchRadius + '.input1X'), force=True)
		mc.connectAttr((AutoSplineRootRig + '.RadiusMagni'), (AutoSplineStratchRadius + '.input2X'), force=True)
		
		
		#直径をコントロールするコンディションを作成します
		Rnum = len(mc.ls('AutoSplineStratchRade_*'))
		AutoSplineStratchRade = mc.shadingNode('condition', asUtility=True, n=('AutoSplineStratchRade_' + str(Rnum + 1)))
		mc.connectAttr((AutoSplineRootRig + '.Radius'), (AutoSplineStratchRade + '.firstTerm'), force=True)
		mc.connectAttr((AutoSplineStratchRadius + '.outputX'), (AutoSplineStratchRade + '.colorIfTrueR'), force=True)
		mc.setAttr(AutoSplineStratchRade + '.operation', 2)
		
		
		#ジョイントのスケールに計算結果を流します
		for i in TrgJoint:
			mc.connectAttr((AutoSplineStratchDiv + '.outputX'), (i + '.scaleX'), force=True)
			mc.connectAttr((AutoSplineStratchRade + '.outColorR'), (i + '.scaleY'), force=True)
			mc.connectAttr((AutoSplineStratchRade + '.outColorR'), (i + '.scaleZ'), force=True)
		
		#スプラインジョイントをセットアップグループに格納します
		TrgRootName = mc.parent(TrgJoint[0], SetupGrp)
		ParentedTrgJoint = mc.listRelatives(TrgRootName, ad=True, f=True)
		ParentedTrgJoint.extend(TrgRootName)
		
		#ルートリグのスケールに対応します
		mc.connectAttr((AutoSplineRootRig + '.scale'),(SetupGrp + '.scale'), force=True)



		#セットアップグループをロックします
		mc.select(GrobalGrp, hi=True)
		LockListGrp = mc.ls(sl=True)
		mc.select(cl=True)
		for i in LockListGrp:
			if 'Grp' in i:
				mc.setAttr(i + '.tx', lock=True)
				mc.setAttr(i + '.ty', lock=True)
				mc.setAttr(i + '.tz', lock=True)
				mc.setAttr(i + '.rx', lock=True)
				mc.setAttr(i + '.ry', lock=True)
				mc.setAttr(i + '.rz', lock=True)
				mc.setAttr(i + '.sx', lock=True)
				mc.setAttr(i + '.sy', lock=True)
				mc.setAttr(i + '.sz', lock=True)
				mc.setAttr(i + '.v', lock=True)
			if 'AutoSplineIKHandle_' in i:
				mc.setAttr(i + ".tx", lock=True)
				mc.setAttr(i + ".ty", lock=True)
				mc.setAttr(i + ".tz", lock=True)
				mc.setAttr(i + ".rx", lock=True)
				mc.setAttr(i + ".ry", lock=True)
				mc.setAttr(i + ".rz", lock=True)
				mc.setAttr(i + ".sx", lock=True)
				mc.setAttr(i + ".sy", lock=True)
				mc.setAttr(i + ".sz", lock=True)
				mc.setAttr(i + ".v",  lock=True)
				mc.setAttr(i + ".pvx", lock=True)
				mc.setAttr(i + ".pvy", lock=True)
				mc.setAttr(i + ".pvz", lock=True)
				mc.setAttr(i + ".off", lock=True)
				mc.setAttr(i + ".rol", lock=True)
				mc.setAttr(i + ".twi", lock=True)
				mc.setAttr(i + ".ikb", lock=True)
		
		for i in IK_Rig_List:
			mc.setAttr(i + ".rx", lock=True)
			mc.setAttr(i + ".ry", lock=True)
			mc.setAttr(i + ".rz", lock=True)
			mc.setAttr(i + ".sx", lock=True)
			mc.setAttr(i + ".sy", lock=True)
			mc.setAttr(i + ".sz", lock=True)
			mc.setAttr(i + ".v",  lock=True)
			mc.setAttr(i + ".rx", keyable=False, channelBox=False)
			mc.setAttr(i + ".ry", keyable=False, channelBox=False)
			mc.setAttr(i + ".rz", keyable=False, channelBox=False)
			mc.setAttr(i + ".sx", keyable=False, channelBox=False)
			mc.setAttr(i + ".sy", keyable=False, channelBox=False)
			mc.setAttr(i + ".sz", keyable=False, channelBox=False)
			mc.setAttr(i + ".v",  keyable=False, channelBox=False)
			
		#オリジナルジョイントをロックします
		for i in OrgJoint:
			mc.setAttr(i + ".tx", lock=True)
			mc.setAttr(i + ".ty", lock=True)
			mc.setAttr(i + ".tz", lock=True)
			mc.setAttr(i + ".rx", lock=True)
			mc.setAttr(i + ".ry", lock=True)
			mc.setAttr(i + ".rz", lock=True)
			mc.setAttr(i + ".sx", lock=True)
			mc.setAttr(i + ".sy", lock=True)
			mc.setAttr(i + ".sz", lock=True)
			mc.setAttr(i + ".v",  lock=True)
		
		#クラスターをロックします
		for i in RenameCluster:
			mc.setAttr(i + ".tx", lock=True)
			mc.setAttr(i + ".ty", lock=True)
			mc.setAttr(i + ".tz", lock=True)
			mc.setAttr(i + ".rx", lock=True)
			mc.setAttr(i + ".ry", lock=True)
			mc.setAttr(i + ".rz", lock=True)
			mc.setAttr(i + ".sx", lock=True)
			mc.setAttr(i + ".sy", lock=True)
			mc.setAttr(i + ".sz", lock=True)
			mc.setAttr(i + ".v",  lock=True)

		#スプラインジョイントをロックします
		for i in ParentedTrgJoint:
			mc.setAttr( i +".tx", keyable=False, channelBox=True)
			mc.setAttr( i +".ty", keyable=False, channelBox=True)
			mc.setAttr( i +".tz", keyable=False, channelBox=True)
			mc.setAttr( i +".rx", keyable=False, channelBox=True)
			mc.setAttr( i +".ry", keyable=False, channelBox=True)
			mc.setAttr( i +".rz", keyable=False, channelBox=True)
			mc.setAttr( i +".sx", keyable=False, channelBox=True)
			mc.setAttr( i +".sy", keyable=False, channelBox=True)
			mc.setAttr( i +".sz", keyable=False, channelBox=True)
			mc.setAttr( i + '.v', lock=True)

		#カーブをロックします		
		mc.setAttr(TagCurve + '.tx', lock=True)
		mc.setAttr(TagCurve + '.ty', lock=True)
		mc.setAttr(TagCurve + '.tz', lock=True)
		mc.setAttr(TagCurve + '.rx', lock=True)
		mc.setAttr(TagCurve + '.ry', lock=True)
		mc.setAttr(TagCurve + '.rz', lock=True)
		mc.setAttr(TagCurve + '.sx', lock=True)
		mc.setAttr(TagCurve + '.sy', lock=True)
		mc.setAttr(TagCurve + '.sz', lock=True)
		mc.setAttr(TagCurve + '.v', lock=True)
		
		
CreateAutoSplineClass().CreateUI()
		
		
		
		

