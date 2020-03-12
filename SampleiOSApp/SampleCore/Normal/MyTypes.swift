//
//  RegularClass.swift
//  SampleCore
//
//  Created by Deffrasnes Ghislain on 17/04/2019.
//  Copyright © 2019 E-Voyageurs Technologies. All rights reserved.
//

protocol MyProtocol {}

extension MyProtocol {
    
}

internal extension String {

    func stringMethod() {
        let myObjcClass = MyObjcClass()
        print(myObjcClass)
    }

}

struct MyStruct {

}

extension MyStruct {

}

enum MyEnum {
    
}


struct ContainerStruct {

    enum ContainedEnum {

    }

    struct InnerContainedStruct {

        enum InnerContainerEnum {

        }

    }

}


extension MyEnum {

}

class MyClass {

    var myVar: ContainerStruct.ContainedEnum?
    var myVar2: ContainerStruct.InnerContainedStruct?
    var myVar3: ContainerStruct.InnerContainedStruct.InnerContainerEnum?

}

extension MyClass {

}
