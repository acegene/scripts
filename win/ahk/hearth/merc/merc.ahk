#SingleInstance Force

;;;; pics are 210 by 50 pixels
Menu, MyMenu, Add, Retire, MenuHandler
Menu, MyMenu, Icon, Retire, %A_ScriptDir%\merc-hotkey-utils\retire.png,, 0
Menu, MyMenu, Add  ; Add a separator line.
Menu, MyMenu, Add, PlayAndAttack, MenuHandler
Menu, MyMenu, Icon, PlayAndAttack, %A_ScriptDir%\merc-hotkey-utils\play-and-attack.png,, 0
Menu, MyMenu, Add  ; Add a separator line.
Menu, MyMenu, Add, Play, MenuHandler
Menu, MyMenu, Icon, Play, %A_ScriptDir%\merc-hotkey-utils\play.png,, 0
Menu, MyMenu, Add  ; Add a separator line.
Menu, MyMenu, Add, Attack, MenuHandler
Menu, MyMenu, Icon, Attack, %A_ScriptDir%\merc-hotkey-utils\attack.png,, 0
Menu, MyMenu, Add  ; Add a separator line.

return

MenuHandler:
    switch A_ThisMenuItem{
        case "Retire": Retire()
        case "PlayAndAttack": PlayAndAttack()
        case "Play": Play()
        case "Attack": Attack()
        default: MsgBox, ERROR: Unexpected menu choice.
    }
	return

!M::Menu, MyMenu, Show  ; i.e. press the Win-Z hotkey to show the menu.

Retire(){
	Run, "%A_ScriptDir%\merc-hotkey-utils\merc-retire.ahk"
}

PlayAndAttack(){
	Run, "%A_ScriptDir%\merc-hotkey-utils\merc-battle.ahk" --play --attack
}

Play(){
	Run, "%A_ScriptDir%\merc-hotkey-utils\merc-battle.ahk" --play
}

Attack(){
	Run, "%A_ScriptDir%\merc-hotkey-utils\merc-battle.ahk" --attack
}

Esc::ExitApp
