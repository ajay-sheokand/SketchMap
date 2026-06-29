@echo off

for %%f in (*.jpg) do (
    copy "%%f" ..\..\_FinalGeneralizedMaps\GeneralizedMaps_location1
)
pause