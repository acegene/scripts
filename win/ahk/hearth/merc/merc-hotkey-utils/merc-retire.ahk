;;;; window must be fullscreen and possibly windowed mode

#include <general-utils>
#include <mouse-utils>

#SingleInstance Force
#NoEnv

SendMode Input
SetWorkingDir %A_ScriptDir%

MouseClickWindowHuman(x_window_ratio, y_window_ratio, x_range, y_range){
    global mouse_navigator
    mouse_navigator.MouseClickWindowHuman(x_window_ratio, y_window_ratio, x_range, y_range)
}

RatioMain(){
    MouseClickWindowHuman(0.403846, 0.917582, 0.08, 0.02) ; view party
    SleepRandom(500)
    MouseClickWindowHuman(0.566506, 0.740385, 0.03, 0.02) ; retire
    SleepRandom(800)
    MouseClickWindowHuman(0.435897, 0.570742, 0.04, 0.02) ; retire confirm
    SleepRandom(300)
    Loop, 14
    {
        MouseClickWindowHuman(0.756010, 0.830357, 0.01, 0.01) ; confirm bounty and party
        SleepRandom(300)
    }
}

;;;; locate hearthstone and bring it to the foreground
SetTitleMatchMode, 2
CoordMode, Mouse, Screen
tt = Hearthstone ahk_class UnityWndClass
WinWait, %tt%
IfWinNotActive, %tt%,, WinActivate, %tt%

;;;; store dimensions of hearthstone in mouse navigator object
WinGetPos, x_window_ratio, y_window_ratio, x_range, y_range, Hearthstone
mouse_navigator := new MouseWindowNavigator(x_window_ratio, y_window_ratio, x_range, y_range)

RatioMain()

RButton::ExitApp
Esc::ExitApp
