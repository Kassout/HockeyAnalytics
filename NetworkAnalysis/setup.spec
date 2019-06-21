# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['network_analytics.py'],
             pathex=['E:\\HockeyAnalytics\\NetworkAnalysis'],
             binaries=[],
             datas=[('welcome_screen.txt', '.'),
                    ('batch_config.txt', '.'),
                    ('datasets/france1819goals.xlsx', 'datasets'),
                    ('datasets/stats indiv.xlsx', 'datasets'),
                    ('datasets/france1819roster.xlsx', 'datasets')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PyQt5'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='network_analytics',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='network_analytics')
