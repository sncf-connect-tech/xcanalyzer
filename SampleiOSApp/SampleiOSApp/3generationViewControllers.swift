//
//  3generationViewControllers.swift
//  SampleiOSApp
//
//  Created by Deffrasnes Ghislain on 27/02/2020.
//  Copyright © 2020 E-Voyageurs Technologies. All rights reserved.
//

import UIKit
import SampleCore


class GrandFatherViewController: UIViewController {

}


class FatherViewController: GrandFatherViewController {

}

class SonViewController: FatherViewController {
    
}


class InheritedFromObjcViewController: ObjcViewController {

}

class Son2ViewController: InheritedFromObjcViewController {

}


class GenericViewController<T>: UIViewController {

}


class InheritedGenericViewController: GenericViewController<Bool> {

}
