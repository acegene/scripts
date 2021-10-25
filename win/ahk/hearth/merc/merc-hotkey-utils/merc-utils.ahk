#SingleInstance Force
#NoEnv

SendMode Input
SetWorkingDir %A_ScriptDir%

GetWindowPercents(byref Xp, byref Yp, Xq, Yq, Xw, Yw, Ww, Hw){
    Xp := (Xq - Xw) / (Ww)
    Yp := (Yq - Yw) / (Hw)
}

GetWindowPercentsCurrent(byref Xp, byref Yp, Xw, Yw, Ww, Hw){
    MouseGetPos, Xc, Yc
    GetWindowPercents(Xp, Yp, Xc, Yc, Xw, Yw, Ww, Hw)
}

SetTitleMatchMode, 2
CoordMode, Mouse, Screen

tt = Hearthstone ahk_class UnityWndClass
WinWait, %tt%
IfWinNotActive, %tt%,, WinActivate, %tt%

WinGetPos, Xw, Yw, Ww, Hw, Hearthstone

LButton::
    global Xw, Yw, Ww, Hw
    GetWindowPercentsCurrent(Xp, Yp, Xw, Yw, Ww, Hw)
    ; MsgBox, You pressed the Left Mouse Button! X%Xp% Y%Yp%
    FileAppend, %Xp% %Yp%`n, *merc-battle-percents.txt
    Return

Esc::ExitApp
